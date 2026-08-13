# Sicherheit

## Pflichtprüfungen

Vor JEDEM Commit:

- [ ] Keine fest verdrahteten Geheimnisse (API-Schlüssel, Passwörter, Token)
- [ ] Alle Nutzereingaben geprüft
- [ ] SQL-Injection ausgeschlossen (parametrisierte Abfragen)
- [ ] XSS ausgeschlossen (bereinigtes HTML)
- [ ] CSRF-Schutz aktiv
- [ ] Authentifizierung und Autorisierung nachgewiesen
- [ ] Rate Limiting auf allen Endpunkten
- [ ] Fehlermeldungen geben nichts Sensibles preis

## Umgang mit Geheimnissen

- Geheimnisse NIE in den Quellcode schreiben
- IMMER Umgebungsvariablen oder einen Secret Manager verwenden
- Beim Start prüfen, dass die benötigten Geheimnisse vorhanden sind
- Jedes möglicherweise offengelegte Geheimnis austauschen

## Vorgehen bei einem Fund

1. SOFORT anhalten
2. Kritische Punkte beheben, bevor es weitergeht
3. Offengelegte Geheimnisse austauschen
4. Die Codebasis auf gleichartige Stellen durchsehen
