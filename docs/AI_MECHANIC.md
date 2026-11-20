# AutoFX AI Mechanic

Asistent obrađuje samo podatke koji su stvarno dobijeni preko ELM327 adaptera. Nema demo izvora podataka niti izmišljenih ECU odgovora.

Dostupna su dva načina rada:

1. **Local analysis (offline)** — fiksna pravila, bez mrežnog zahteva i bez slobodnog LLM razgovora.
2. **OpenAI cloud (explicit opt-in)** — OpenAI API uz poseban ključ, uputstvo u [README](../README.md).

Bez stvarnog očitavanja AI Assistant prikazuje obaveštenje da podaci nisu dostupni. Cloud model dobija ograničeni snimak dostupnih PID-ova i DTC-ova, a ne pristup ECU komandama.

AI može da predlaže naredne provere, ali ne može samostalno izvršiti brisanje DTC kodova, servisne adaptacije ili izmene ECU konfiguracije.
