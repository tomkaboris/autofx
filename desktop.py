"""AutoFX Desktop — professional read-only OBD-II diagnostic workstation.

Launch with: python desktop.py
"""
from __future__ import annotations

import json
from queue import Empty, Queue
import sys
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import pyqtgraph as pg
from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QInputDialog, QLineEdit, QMainWindow, QMessageBox, QPushButton, QStackedWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)
from serial.tools import list_ports

from obd_ai.adapter import Elm327Adapter
from obd_ai.ai_mechanic import answer, diagnostic_context
from obd_ai.profiles import PROFILES, profile_for_question
from obd_ai.service_operations import CONFIRMATION_TEXT, OperationDenied, operation_description, validate_clear_request

BG = "#0b111b"
PANEL = "#141e2c"
PANEL2 = "#1b293a"
BORDER = "#2b394b"
FG = "#e6edf6"
MUTED = "#8b9aae"
ACCENT = "#4cb7ff"
GREEN = "#3dd6a4"
ORANGE = "#f5ba64"


class Acquisition(QThread):
    """Keep all serial queries off the GUI thread; never issue ECU writes."""

    connected = Signal(str)
    identification = Signal(dict)
    sample = Signal(dict)
    faults = Signal(list)
    profile_result = Signal(dict)
    service_result = Signal(dict)
    failed = Signal(str)
    finished_session = Signal(str)

    def __init__(self, port: str, interval: float = 1.5):
        super().__init__()
        self.mode, self.port, self.interval = "vehicle", port, interval
        self._stop = threading.Event()
        self._profile_requests = Queue(maxsize=1)
        self._service_requests = Queue(maxsize=1)

    def request_profile(self, key: str) -> bool:
        if self._stop.is_set() or not self.isRunning():
            return False
        try:
            self._profile_requests.put_nowait(key)
        except Exception:
            return False
        return True

    def request_service(self, authorization: dict) -> bool:
        if self._stop.is_set() or not self.isRunning():
            return False
        try:
            self._service_requests.put_nowait(dict(authorization))
            return True
        except Exception:
            return False

    def stop(self):
        self._stop.set()

    def run(self):
        adapter = Elm327Adapter(self.port)
        output = Path("logs") / ("desktop-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".jsonl")
        try:
            self.connected.emit(adapter.connect())
            try:
                # VIN stays in memory, not in JSONL session logs or AI requests.
                self.identification.emit(adapter.identify_vehicle())
            except Exception as exc:
                self.failed.emit("Vehicle identification unavailable: " + str(exc))
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("a", encoding="utf-8") as stream:
                try:
                    codes = adapter.dtcs()
                    stream.write(json.dumps({"type": "dtcs", "codes": codes}) + "\n")
                    self.faults.emit(codes)
                except Exception as exc:
                    stream.write(json.dumps({"type": "dtc_error", "message": str(exc)}) + "\n")
                    self.failed.emit("DTC read failed: " + str(exc))
                while not self._stop.is_set():
                    try:
                        service_request = self._service_requests.get_nowait()
                    except Empty:
                        service_request = None
                    if service_request is not None and not self._stop.is_set():
                        # Re-read immediately before the write; never trust stale GUI data.
                        fresh = adapter.read()
                        try:
                            validate_clear_request(
                                mode=self.mode, sample=fresh,
                                confirmed=service_request.get("confirmed", False),
                                text=service_request.get("text", ""),
                            )
                            before = adapter.dtcs()
                            stream.write(json.dumps({"type": "service_before", "dtcs": before}) + "\n")
                            stream.flush()
                            result = adapter.clear_emissions_dtcs()
                            result["before"] = before
                        except Exception as exc:
                            result = {"operation": "clear_emissions_dtc_mode04",
                                      "mode": self.mode, "result": "denied_or_failed",
                                      "error": str(exc)}
                        result["timestamp"] = datetime.now().isoformat()
                        stream.write(json.dumps({"type": "service_result", **result}) + "\n")
                        stream.flush()
                        self.service_result.emit(result)
                        if result.get("after") is not None:
                            self.faults.emit(result["after"])
                    try:
                        requested = self._profile_requests.get_nowait()
                    except Empty:
                        requested = None
                    if requested is not None and not self._stop.is_set():
                        try:
                            scan = adapter.read_profile(requested)
                            scan["timestamp"] = datetime.now().isoformat()
                            stream.write(json.dumps({"type": "profile_scan", **scan}) + "\n")
                            stream.flush()
                            self.profile_result.emit(scan)
                        except Exception as exc:
                            self.failed.emit("Profile scan failed: " + str(exc))
                    started = time.monotonic()
                    reading = adapter.read()
                    stream.write(json.dumps({"type": "telemetry", **reading}) + "\n")
                    stream.flush()
                    self.sample.emit(reading)
                    self._stop.wait(max(0, self.interval - (time.monotonic() - started)))
            self.finished_session.emit(str(output))
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            try:
                adapter.close()
            except Exception:
                pass


class AnalysisWorker(QThread):
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, question: str, snapshot: dict, provider: str):
        super().__init__()
        self.question, self.snapshot, self.provider = question, snapshot, provider

    def run(self):
        try:
            self.completed.emit(answer(self.question, self.snapshot, self.provider))
        except Exception as exc:
            self.failed.emit(str(exc))


def label(text, size=12, color=FG, bold=False):
    item = QLabel(text)
    font = QFont("Segoe UI", size)
    font.setBold(bold)
    item.setFont(font)
    item.setStyleSheet("color: " + color + "; background: transparent;")
    return item


def panel():
    frame = QFrame()
    frame.setObjectName("panel")
    return frame


class StatCard(QFrame):
    def __init__(self, title, unit):
        super().__init__()
        self.setObjectName("panel")
        column = QVBoxLayout(self)
        column.setContentsMargins(20, 18, 20, 18)
        column.setSpacing(10)
        column.addWidget(label(title.upper(), 10, MUTED, True))
        row = QHBoxLayout()
        self.value = label("—", 30, FG, True)
        row.addWidget(self.value)
        row.addStretch()
        row.addWidget(label(unit, 11, MUTED))
        column.addLayout(row)

    def update_value(self, value):
        self.value.setText("—" if value is None else f"{value:,.0f}")


class AutoFX(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoFX  |  Automotive Diagnostics")
        self.resize(1380, 850)
        self.setMinimumSize(1040, 680)
        self.worker = None
        self.ai_worker = None
        self.last_sample = None
        self.vehicle_identity = None
        for field in self.identity_fields.values():
            field.setText("Unavailable")
        self.identity_pids.setRowCount(0)
        self.identity_note.setText("Waiting for real ECU identity; no values are inferred.")
        self.current_codes = []
        self.last_scan = None
        self.vehicle_identity = None
        self.last_sample_received = 0.0
        self.history = deque(maxlen=90)
        self.tick = 0
        self.session_path = "No session saved yet"
        self.setStyleSheet(STYLE)
        self.build_ui()
        self.refresh_ports()

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        row = QHBoxLayout(root)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(224)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(18, 26, 18, 22)
        nav.setSpacing(10)
        nav.addWidget(label("◈  AutoFX", 24, FG, True))
        nav.addWidget(label("AUTOMOTIVE DIAGNOSTICS", 9, MUTED, True))
        nav.addSpacing(30)
        self.nav_buttons = []
        for name in ("Overview", "Vehicle", "Diagnostics", "Sessions", "AI Assistant"):
            b = QPushButton(name)
            b.setProperty("nav", True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, n=len(self.nav_buttons): self.show_page(n))
            self.nav_buttons.append(b)
            nav.addWidget(b)
        nav.addStretch()
        nav.addWidget(label("ENGINEERING WORKSTATION", 9, MUTED))
        nav.addWidget(label("REAL VEHICLE · SERVICE WORKSPACE", 10, GREEN, True))
        row.addWidget(sidebar)

        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(18)
        head = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label("Vehicle workspace", 23, FG, True))
        titles.addWidget(label("Live diagnostics · ELM327 Bluetooth Classic", 11, MUTED))
        head.addLayout(titles)
        head.addStretch()
        self.status = label("●  DISCONNECTED", 11, MUTED, True)
        head.addWidget(self.status)
        layout.addLayout(head)

        bar = panel()
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(16, 12, 16, 12)
        bar_layout.addWidget(label("ELM327 SERIAL · REAL VEHICLE ONLY", 10, GREEN, True))
        bar_layout.addSpacing(12)
        bar_layout.addWidget(label("PORT", 10, MUTED, True))
        self.ports = QComboBox()
        self.ports.setEditable(True)
        self.ports.setMinimumWidth(160)
        bar_layout.addWidget(self.ports)
        reload_button = QPushButton("↻")
        reload_button.setFixedWidth(40)
        reload_button.clicked.connect(self.refresh_ports)
        bar_layout.addWidget(reload_button)
        bar_layout.addStretch()
        self.connect_button = QPushButton("Connect")
        self.connect_button.setObjectName("primary")
        self.connect_button.clicked.connect(self.toggle_connection)
        bar_layout.addWidget(self.connect_button)
        layout.addWidget(bar)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.overview_page())
        self.pages.addWidget(self.vehicle_page())
        self.pages.addWidget(self.diagnostics_page())
        self.pages.addWidget(self.sessions_page())
        self.pages.addWidget(self.ai_page())
        layout.addWidget(self.pages, 1)

        self.footer = label("Connect a real ELM327 adapter to start a diagnostic session", 10, MUTED)
        layout.addWidget(self.footer)
        row.addWidget(workspace, 1)
        self.show_page(0)

    def overview_page(self):
        page = QWidget()
        main = QVBoxLayout(page)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(16)
        heading = QHBoxLayout()
        heading.addWidget(label("Live engine telemetry", 16, FG, True))
        heading.addStretch()
        heading.addWidget(label("STANDARD OBD-II PIDs", 10, MUTED))
        main.addLayout(heading)
        grid = QGridLayout()
        grid.setSpacing(14)
        self.cards = {}
        for idx, (key, title, unit) in enumerate((
            ("RPM", "Engine RPM", "rpm"),
            ("SPEED", "Vehicle speed", "km/h"),
            ("COOLANT_TEMP", "Coolant temperature", "°C"),
            ("ENGINE_LOAD", "Engine load", "%"),
            ("THROTTLE_POS", "Throttle position", "%"),
        )):
            card = StatCard(title, unit)
            self.cards[key] = card
            grid.addWidget(card, idx // 3, idx % 3)
        main.addLayout(grid)
        chart_box = panel()
        graph_layout = QVBoxLayout(chart_box)
        graph_layout.setContentsMargins(18, 16, 18, 16)
        graph_layout.addWidget(label("RPM · LIVE TREND", 11, FG, True))
        self.graph = pg.PlotWidget()
        self.graph.setBackground(PANEL)
        self.graph.showGrid(x=True, y=True, alpha=0.15)
        self.graph.getAxis("bottom").setPen(pg.mkPen(MUTED))
        self.graph.getAxis("left").setPen(pg.mkPen(MUTED))
        self.graph.setLabel("left", "RPM")
        self.graph.setLabel("bottom", "Sample")
        self.curve = self.graph.plot([], [], pen=pg.mkPen(ACCENT, width=2))
        graph_layout.addWidget(self.graph)
        main.addWidget(chart_box, 1)
        return page

    def vehicle_page(self):
        page = QWidget()
        main = QVBoxLayout(page)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(14)
        main.addWidget(label("Vehicle & ECU identification", 19, FG, True))
        main.addWidget(label("Live Mode 09 identity and ECU-advertised generic PID support", 11, MUTED))
        card = panel()
        details = QGridLayout(card)
        details.setContentsMargins(18, 18, 18, 18)
        self.identity_fields = {}
        names = (
            ("vin", "VIN"), ("vin_status", "VIN status"),
            ("protocol", "OBD protocol"), ("port", "Adapter port"),
            ("calibration_id", "Calibration ID"), ("calibration_verification", "CVN"),
        )
        for row, (key, title) in enumerate(names):
            details.addWidget(label(title, 11, MUTED), row, 0)
            value = label("Unavailable", 12, FG)
            value.setWordWrap(True)
            self.identity_fields[key] = value
            details.addWidget(value, row, 1)
        details.setColumnStretch(1, 1)
        main.addWidget(card)
        main.addWidget(label("GENERIC MODE 01 PID SUPPORT", 11, FG, True))
        self.identity_pids = QTableWidget(0, 2)
        self.identity_pids.setHorizontalHeaderLabels(["PID", "ADVERTISED SUPPORT"])
        self.identity_pids.horizontalHeader().setStretchLastSection(True)
        self.identity_pids.verticalHeader().hide()
        self.identity_pids.setEditTriggers(QTableWidget.NoEditTriggers)
        main.addWidget(self.identity_pids, 1)
        self.identity_note = label(
            "Connect to a real ECU. No VIN, ECU ID or capabilities are inferred.", 11, ORANGE
        )
        self.identity_note.setWordWrap(True)
        main.addWidget(self.identity_note)
        return page

    def on_identification(self, result):
        self.vehicle_identity = dict(result)
        for key, field in self.identity_fields.items():
            field.setText(str(result.get(key) or "Unavailable"))
        pids = result.get("supported_pids", {})
        self.identity_pids.setRowCount(len(pids))
        for row, (pid, supported) in enumerate(sorted(pids.items())):
            self.identity_pids.setItem(row, 0, QTableWidgetItem(pid))
            self.identity_pids.setItem(row, 1, QTableWidgetItem(
                "Supported" if supported else "Not advertised / unsupported"
            ))
        self.identity_note.setText(
            f"Available generic PIDs: {result.get('supported_count', 0)} / "
            f"{result.get('total_checked', 0)} checked. "
            "This is not a full OEM ECU/module inventory. "
            "VIN is displayed locally and is not sent to AI by default."
        )

    def diagnostics_page(self):
        page = QWidget()
        main = QVBoxLayout(page)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(12)
        main.addWidget(label("DTC Service Workspace", 19, FG, True))
        main.addWidget(label("Select a code to inspect it. Mode 04 clearing affects all supported emissions-related DTCs.", 11, MUTED))
        self.dtc_table = QTableWidget(0, 2)
        self.dtc_table.setHorizontalHeaderLabels(["CODE", "DESCRIPTION"])
        self.dtc_table.horizontalHeader().setStretchLastSection(True)
        self.dtc_table.setAlternatingRowColors(True)
        self.dtc_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.dtc_table.setSelectionMode(QTableWidget.SingleSelection)
        self.dtc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.dtc_table.verticalHeader().hide()
        self.dtc_table.itemSelectionChanged.connect(self.show_dtc_detail)
        main.addWidget(self.dtc_table, 2)

        details = panel()
        details_layout = QVBoxLayout(details)
        details_layout.addWidget(label("SELECTED FAULT", 10, MUTED, True))
        self.dtc_title = label("No DTC selected", 15, FG, True)
        details_layout.addWidget(self.dtc_title)
        self.dtc_detail = label("Select a row above to see diagnostic guidance.", 11, MUTED)
        self.dtc_detail.setWordWrap(True)
        details_layout.addWidget(self.dtc_detail)
        ask_row = QHBoxLayout()
        self.dtc_ask_ai = QPushButton("Discuss selected code with AI")
        self.dtc_ask_ai.clicked.connect(self.ask_selected_dtc)
        ask_row.addWidget(self.dtc_ask_ai)
        ask_row.addStretch()
        details_layout.addLayout(ask_row)
        main.addWidget(details, 1)

        service = panel()
        service_layout = QVBoxLayout(service)
        service_layout.addWidget(label("SERVICE OPERATION · GLOBAL DTC CLEAR", 11, ORANGE, True))
        service_description = label(
            "Mode 04 clears ALL supported emission-related codes, may erase freeze frames and resets readiness. "
            "It does not selectively erase this row. Engine OFF and vehicle stationary required.", 11, MUTED
        )
        service_description.setWordWrap(True)
        service_layout.addWidget(service_description)
        service_actions = QHBoxLayout()
        self.dtc_clear_button = QPushButton("Clear emissions DTCs (Mode 04)")
        self.dtc_clear_button.clicked.connect(self.confirm_clear_dtcs)
        service_actions.addWidget(self.dtc_clear_button)
        service_actions.addStretch()
        service_layout.addLayout(service_actions)
        self.service_note = label("Operator confirmation + fresh RPM=0 / SPEED=0 required.", 10, ORANGE)
        self.service_note.setWordWrap(True)
        service_layout.addWidget(self.service_note)
        main.addWidget(service)
        return page

    def show_dtc_detail(self):
        row = self.dtc_table.currentRow()
        if not (0 <= row < len(self.current_codes)):
            self.dtc_title.setText("No DTC selected")
            self.dtc_detail.setText("Select a stored DTC to inspect it.")
            return
        code = self.current_codes[row]
        self.dtc_title.setText(str(code.get("code", "Unknown")))
        self.dtc_detail.setText(
            str(code.get("description", "No description available")) +
            "\nSuggested workflow: save the diagnostic session, inspect related live data, "
            "consult manufacturer procedures, and verify the repair. A DTC is not proof of one specific cause."
        )

    def ask_selected_dtc(self):
        row = self.dtc_table.currentRow()
        if not (0 <= row < len(self.current_codes)):
            QMessageBox.information(self, "Select a DTC", "Choose a fault in the table first.")
            return
        code = self.current_codes[row]
        question = ("Objasni DTC " + str(code.get("code", "")) +
                    " i njegove moguće uzroke. Predloži bezbedne servisne provere pre brisanja.")
        self.show_page(4)
        self.start_analysis(question)

    def confirm_clear_dtcs(self):
        if self.worker is None or not self.worker.isRunning():
            QMessageBox.warning(self, "No ECU", "Connect a real ELM327 adapter first.")
            return
        if self.last_sample is None:
            QMessageBox.warning(self, "No live reading", "Wait for current RPM and SPEED readings.")
            return
        consent = QMessageBox.warning(
            self, "Confirm global OBD-II Mode 04",
            operation_description() + "\n\nOnly continue after documenting current faults. Is the engine OFF?",
            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel,
        )
        if consent != QMessageBox.Yes:
            return
        typed, ok = QInputDialog.getText(
            self, "Second confirmation",
            "Type CLEAR ALL to authorize one global emissions-related DTC clear:"
        )
        if not ok:
            return
        try:
            validate_clear_request(mode=self.worker.mode, sample=self.last_sample,
                                   confirmed=True, text=typed)
        except OperationDenied as exc:
            QMessageBox.warning(self, "Operation blocked", str(exc))
            return
        if not self.worker.request_service({"confirmed": True, "text": typed}):
            QMessageBox.warning(self, "Busy", "Another service operation is pending.")
            return
        self.dtc_clear_button.setEnabled(False)
        self.service_note.setText("Service request queued. ECU state will be rechecked before execution.")

    def on_service_result(self, result):
        self.dtc_clear_button.setEnabled(True)
        message = ("Mode 04: " + str(result.get("result", "unknown")) +
                   (". " + str(result.get("error")) if result.get("error") else "") +
                   ". Inspect the new DTC reading to verify the outcome.")
        self.service_note.setText(message)
        self.sessions_text.append("\nSERVICE: " + json.dumps(result, ensure_ascii=False))
        if result.get("error"):
            QMessageBox.warning(self, "Service result", message)
        else:
            QMessageBox.information(self, "Service result", message)

    def sessions_page(self):
        page = QWidget()
        main = QVBoxLayout(page)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(label("Diagnostic sessions", 17, FG, True))
        main.addWidget(label("Each session writes telemetry to a local JSONL log.", 11, MUTED))
        self.sessions_text = QTextEdit()
        self.sessions_text.setReadOnly(True)
        self.sessions_text.setPlainText("Connect the real ELM327 serial adapter to record a session.\n\nLogs are saved under ./logs/ and are excluded from Git.")
        main.addWidget(self.sessions_text, 1)
        return page

    def ai_page(self):
        page = QWidget()
        main = QVBoxLayout(page)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(15)
        main.addWidget(label("AI Mechanic · diagnostic assistant", 17, FG, True))
        main.addWidget(label("Read-only analysis of current OBD values and stored trouble codes", 11, MUTED))
        settings = panel()
        controls = QHBoxLayout(settings)
        controls.addWidget(label("ANALYSIS MODE", 10, MUTED, True))
        self.ai_provider = QComboBox()
        self.ai_provider.addItems(["Local analysis (offline)", "OpenAI cloud (explicit opt-in)"])
        controls.addWidget(self.ai_provider)
        controls.addStretch()
        self.ai_snapshot_status = label("No snapshot available", 10, ORANGE)
        controls.addWidget(self.ai_snapshot_status)
        main.addWidget(settings)

        scan_panel = panel()
        scan_layout = QVBoxLayout(scan_panel)
        scan_layout.addWidget(label("TARGETED READ-ONLY DIAGNOSTICS", 11, FG, True))
        scan_row = QHBoxLayout()
        self.scan_profile = QComboBox()
        for key, item in PROFILES.items():
            self.scan_profile.addItem(item.title, key)
        scan_row.addWidget(self.scan_profile, 1)
        self.scan_button = QPushButton("Read selected PIDs")
        self.scan_button.clicked.connect(self.request_diagnostic_scan)
        scan_row.addWidget(self.scan_button)
        scan_layout.addLayout(scan_row)
        self.scan_note = label("Profiles use standard Mode 01 reads; unsupported PIDs remain unavailable.", 10, MUTED)
        scan_note_text = "DPF/SCR: generic context only; OEM data needed for soot, NOx and dosing."
        scan_layout.addWidget(self.scan_note)
        scan_layout.addWidget(label(scan_note_text, 10, ORANGE))
        self.scan_results = QTableWidget(0, 3)
        self.scan_results.setHorizontalHeaderLabels(["PID", "VALUE", "STATUS"])
        self.scan_results.horizontalHeader().setStretchLastSection(True)
        self.scan_results.verticalHeader().hide()
        self.scan_results.setEditTriggers(QTableWidget.NoEditTriggers)
        self.scan_results.setMaximumHeight(180)
        scan_layout.addWidget(self.scan_results)
        main.addWidget(scan_panel)
        self.ai_chat = QTextEdit()
        self.ai_chat.setReadOnly(True)
        self.ai_chat.setPlainText(
            "AutoFX AI Mechanic\n\n"
            "Poveži stvarni ECU i postavi pitanje ili klikni Analyze snapshot.\n"
            "Local analysis koristi ugrađena pravila bez API-ja. OpenAI režim zahteva OPENAI_API_KEY "
            "i šalje trenutna očitavanja i pitanje cloud servisu.\n\n"
            "Ovaj asistent nikada ne šalje komande ECU-u."
        )
        main.addWidget(self.ai_chat, 1)
        question_row = QHBoxLayout()
        self.ai_question = QLineEdit()
        self.ai_question.setPlaceholderText("Npr. Šta znače ove greške i koje provere preporučuješ?")
        self.ai_question.returnPressed.connect(self.ask_ai)
        question_row.addWidget(self.ai_question, 1)
        self.ai_send = QPushButton("Ask AI")
        self.ai_send.setObjectName("primary")
        self.ai_send.clicked.connect(self.ask_ai)
        question_row.addWidget(self.ai_send)
        main.addLayout(question_row)
        actions = QHBoxLayout()
        self.ai_analyze = QPushButton("Analyze snapshot")
        self.ai_analyze.clicked.connect(self.analyze_snapshot)
        actions.addWidget(self.ai_analyze)
        actions.addStretch()
        actions.addWidget(label("Cloud sends a limited snapshot only on request", 10, MUTED))
        main.addLayout(actions)
        return page

    def request_diagnostic_scan(self):
        key = self.scan_profile.currentData()
        if self.worker is None or not self.worker.isRunning():
            self.scan_note.setText("First connect a real vehicle.")
            return
        if self.worker.request_profile(key):
            self.scan_button.setEnabled(False)
            self.scan_note.setText("Reading " + str(key).upper() + " profile on the OBD acquisition thread …")
        else:
            self.scan_note.setText("Scan already queued, or adapter is disconnecting.")

    def on_profile_scan(self, scan):
        self.last_scan = dict(scan)
        readings = scan.get("readings", {})
        self.scan_results.setRowCount(len(readings))
        for row, (name, reading) in enumerate(readings.items()):
            value = reading.get("value")
            unit = reading.get("unit") or ""
            self.scan_results.setItem(row, 0, QTableWidgetItem(name))
            self.scan_results.setItem(row, 1, QTableWidgetItem("—" if value is None else f"{value} {unit}"))
            self.scan_results.setItem(row, 2, QTableWidgetItem(str(reading.get("status", "unknown"))))
        self.scan_note.setText("Completed " + str(scan.get("profile", "")).upper() + " · status shown per PID")
        self.scan_button.setEnabled(True)

    def analyze_snapshot(self):
        self.start_analysis("Analiziraj trenutno stanje motora i DTC kodove; predloži redosled bezbednih provera.")

    def ask_ai(self):
        question = self.ai_question.text().strip()
        if question:
            suggested = profile_for_question(question)
            for index in range(self.scan_profile.count()):
                if self.scan_profile.itemData(index) == suggested:
                    self.scan_profile.setCurrentIndex(index)
                    break
            self.start_analysis(question)
            self.ai_question.clear()

    def start_analysis(self, question):
        if self.ai_worker is not None and self.ai_worker.isRunning():
            return
        if self.last_sample is None:
            self.ai_chat.append("\n[AutoFX] Nema aktivnih očitavanja. Poveži stvarni ECU.")
            return
        provider = "openai" if self.ai_provider.currentIndex() == 1 else "offline"
        snapshot = diagnostic_context(self.last_sample, self.current_codes, self.last_scan)
        self.ai_chat.append("\nTEHNIČAR: " + question)
        self.ai_chat.append("\nAutoFX: Analiziram trenutni snimak …")
        self.ai_send.setEnabled(False)
        self.ai_analyze.setEnabled(False)
        self.ai_worker = AnalysisWorker(question, snapshot, provider)
        self.ai_worker.completed.connect(self.on_ai_answer)
        self.ai_worker.failed.connect(self.on_ai_failure)
        self.ai_worker.finished.connect(self.on_ai_finished)
        self.ai_worker.start()

    def on_ai_answer(self, text):
        self.ai_chat.append("\nAI MECHANIC:\n" + text + "\n")

    def on_ai_failure(self, message):
        self.ai_chat.append("\nGREŠKA: " + message + "\n")

    def on_ai_finished(self):
        self.ai_send.setEnabled(True)
        self.ai_analyze.setEnabled(True)

    def show_page(self, index):
        self.pages.setCurrentIndex(index)
        for n, button in enumerate(self.nav_buttons):
            button.setProperty("selected", n == index)
            button.style().unpolish(button)
            button.style().polish(button)

    def refresh_ports(self):
        current = self.ports.currentText()
        self.ports.clear()
        self.ports.addItems([p.device for p in list_ports.comports()])
        if current:
            self.ports.setEditText(current)
        if not self.ports.currentText():
            self.ports.setEditText("/dev/rfcomm0" if sys.platform.startswith("linux") else "COM5")

    def toggle_connection(self):
        if self.worker and self.worker.isRunning():
            self.connect_button.setEnabled(False)
            self.worker.stop()
            self.status.setText("●  DISCONNECTING")
            return
        port = self.ports.currentText().strip()
        if not port:
            QMessageBox.warning(self, "Port required", "Select the ELM327 serial port.")
            return
        self.worker = Acquisition(port)
        self.worker.connected.connect(self.on_connected)
        self.worker.identification.connect(self.on_identification)
        self.worker.sample.connect(self.on_sample)
        self.worker.faults.connect(self.on_faults)
        self.worker.profile_result.connect(self.on_profile_scan)
        self.worker.service_result.connect(self.on_service_result)
        self.worker.failed.connect(self.on_error)
        self.worker.finished_session.connect(self.on_saved)
        self.worker.finished.connect(self.on_stopped)
        self.connect_button.setText("Disconnect")
        self.ports.setEnabled(False)
        self.status.setText("●  CONNECTING")
        self.footer.setText("Opening OBD connection …")
        self.history.clear()
        self.last_sample = None
        self.current_codes = []
        self.last_scan = None
        self.dtc_clear_button.setEnabled(True)
        self.scan_results.setRowCount(0)
        self.scan_button.setEnabled(True)
        self.dtc_table.setRowCount(0)
        self.ai_snapshot_status.setText("Waiting for telemetry")
        self.tick = 0
        self.worker.start()

    def on_connected(self, description):
        self.status.setText("●  ECU CONNECTED")
        self.status.setStyleSheet("color: " + GREEN + ";")
        self.footer.setText(description)

    def on_sample(self, sample):
        self.last_sample = dict(sample)
        self.ai_snapshot_status.setText("Snapshot ready · " + str(sample.get("mode", "unknown")).upper())
        values = sample.get("sensors", {})
        for key, card in self.cards.items():
            card.update_value(values.get(key))
        rpm = values.get("RPM")
        self.history.append((self.tick, float(rpm) if rpm is not None else float("nan")))
        self.tick += 1
        self.curve.setData([x for x, _ in self.history], [y for _, y in self.history])

    def on_faults(self, codes):
        self.current_codes = list(codes)
        self.dtc_table.setRowCount(len(codes))
        for row, item in enumerate(codes):
            self.dtc_table.setItem(row, 0, QTableWidgetItem(str(item.get("code", ""))))
            self.dtc_table.setItem(row, 1, QTableWidgetItem(str(item.get("description", ""))))

    def on_error(self, message):
        if message.startswith("Profile scan failed:"):
            self.scan_button.setEnabled(True)
            self.scan_note.setText(message)
        self.footer.setText("Error: " + message)
        if not (message.startswith("DTC read failed") or message.startswith("Vehicle identification unavailable:")):
            QMessageBox.warning(self, "AutoFX connection", message)

    def on_saved(self, path):
        self.session_path = path
        self.sessions_text.append("\nSaved: " + path)

    def on_stopped(self):
        self.vehicle_identity = None
        for field in self.identity_fields.values():
            field.setText("Unavailable")
        self.identity_pids.setRowCount(0)
        self.identity_note.setText("Disconnected. Connect a real ECU to read identity.")
        self.dtc_clear_button.setEnabled(True)
        self.status.setText("●  DISCONNECTED")
        self.status.setStyleSheet("color: " + MUTED + ";")
        self.connect_button.setText("Connect")
        self.connect_button.setEnabled(True)
        self.scan_button.setEnabled(True)
        self.ports.setEnabled(True)

    def closeEvent(self, event):
        if self.ai_worker is not None and self.ai_worker.isRunning():
            event.ignore()
            self.footer.setText("AI request still running. Close after the answer arrives.")
            return
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            if not self.worker.wait(5000):
                event.ignore()
                self.footer.setText("Waiting for serial read to finish before closing …")
                return
        event.accept()


STYLE = """
QMainWindow, QWidget { background: #0b111b; color: #e6edf6; font-family: 'Segoe UI', 'Inter', sans-serif; }
QFrame#sidebar { background: #101926; border-right: 1px solid #293546; }
QFrame#panel { background: #141e2c; border: 1px solid #29384b; border-radius: 13px; }
QPushButton { color: #dce8f5; background: #233347; padding: 10px 15px; border: 1px solid #33465e; border-radius: 8px; font-weight: 600; }
QPushButton:hover { background: #30445c; }
QPushButton#primary { background: #187dd6; border: 1px solid #2698f2; color: white; padding: 12px 24px; }
QPushButton#primary:hover { background: #2394ec; }
QPushButton[nav="true"] { text-align: left; background: transparent; border: 0; padding: 14px; color: #94a6bc; }
QPushButton[nav="true"]:hover { background: #1b2b3d; }
QPushButton[selected="true"] { background: #1d344a; color: #63c4ff; border-left: 3px solid #4cb7ff; }
QComboBox, QLineEdit, QTextEdit, QTableWidget { background: #111b28; color: #e6edf6; border: 1px solid #304156; border-radius: 7px; padding: 8px; }
QComboBox QAbstractItemView { background: #1b293a; color: #e6edf6; selection-background-color: #28577b; }
QTableWidget { gridline-color: #29384b; alternate-background-color: #172333; }
QHeaderView::section { background: #1b293a; color: #a9bbcc; padding: 12px; border: 0; }
QScrollBar:vertical { background: #152231; width: 10px; }
QScrollBar::handle:vertical { background: #40566c; border-radius: 4px; }
"""

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = AutoFX()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
