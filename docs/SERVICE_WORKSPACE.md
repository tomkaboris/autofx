# DTC Service Workspace — real vehicle only

Na ekranu **Diagnostics** izaberi očitani DTC kod za detalje i razgovor sa AI asistentom.

**Clear emissions DTCs (Mode 04)** je stvarna ECU servisna komanda, ne simulator. Zahteva:
- povezan stvarni ECU;
- vozilo zaustavljeno i motor ugašen;
- sveža RPM=0 i SPEED=0 ECU očitavanja;
- dve izričite potvrde servisera.

Komanda je globalna za podržane emisijske DTC podatke. Može obrisati freeze-frame i resetovati readiness monitore; ne briše selektivno jednu stavku. Trajni kodovi i proizvođački DTC-ovi mogu ostati. Pre intervencije sačuvaj kodove i prateće informacije.

Nakon zahteva AutoFX ponovo čita DTC kodove. Ovaj rezultat nije dokaz da je kvar popravljen; neponovljen ili nedostupan odgovor nije potvrda uspeha.

**Ne testiraj brisanje na klijentskom vozilu bez saglasnosti i potrebne procedure.** Real ECU tok pisanja nije verifikovan na svim uređajima.

Interfejs za proizvođački podržane adaptacije još nije implementiran. Proizvoljan editor ECU parametara nije deo trenutne aplikacije.
