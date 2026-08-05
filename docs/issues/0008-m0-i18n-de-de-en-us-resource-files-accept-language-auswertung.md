---
id: "0008"
title: M0: i18n - de-DE/en-US Resource-Files + Accept-Language-Auswertung
status: open
milestone: M0
type: AFK
---

# M0: i18n - de-DE/en-US Resource-Files + Accept-Language-Auswertung

## Parent

Meilenstein [M0](docs/milestones/m0-projekt-grundgeruest.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Resource-Files-Mechanismus fuer Fehlermeldungen/serverseitige Texte in de-DE (Default) und en-US, ausgewaehlt ueber den Accept-Language-Header (Abschnitt 0.9).

## Acceptance criteria

- [ ] Derselbe Domaenenfehler liefert je nach Accept-Language-Header title/detail auf Deutsch oder Englisch
- [ ] Fehlt der Header, ist de-DE der Default
- [ ] Neue Fehlertexte werden zentral in den Resource-Files gepflegt, nicht inline im Code

## Blocked by

- Blocked by [0005](0005-m0-shared-kernel-rfc-7807-problemdetails-exception-handler.md)
