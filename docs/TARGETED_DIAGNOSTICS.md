# Targeted diagnostics — stvarni ECU podaci

Profili **Engine, EGR, DPF i SCR** čitaju dostupne generičke Mode 01 PID-ove preko povezanog ELM327 adaptera.

Postupak: poveži stvarni ECU → izaberi profil u AI Assistant ekranu → **Read selected PIDs** → pogledaj stvarne vrednosti i status podrške → **Analyze snapshot**.

Nema simuliranih vrednosti. Svaki nepodržani PID prikazuje se kao **unsupported**, a neuspešno očitavanje kao **unavailable/error**.

DPF i SCR profili ne garantuju pristup količini čađi, diferencijalnom pritisku, NOx očitavanjima ili AdBlue doziranju. Za takve OEM podatke potreban je odgovarajući ECU profil i alat.

Nema automatskog ECU pisanja niti proizvoljnih CAN komandi. Više informacija u [README](../README.md).
