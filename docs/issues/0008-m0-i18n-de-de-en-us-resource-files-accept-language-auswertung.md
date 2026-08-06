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

## Stand: zurueckgestellt ans Ende, PR #9 geschlossen

Ein erster Anlauf (Branch `0008-…`, PR #9) wurde **geschlossen, nicht gemergt**. Kerndefekt:
`src/shared_kernel/i18n/middleware.py` und `src/shared_kernel/resources/provider.py` legten eine
Starlette-Middleware und dateibasiertes Ressourcen-Laden in die dependency-freie Domaenenschicht;
zusaetzlich verletzte der Code durchgaengig die Stilregeln (kein Pattern Matching, Exceptions statt
`Result`, imperativ statt deklarativ). Der Branch bleibt als Vorlage erhalten.

**Platzierung beim Neubau:** Sprachauswahl ist **kein** Kerngeschaeft, sondern ein
Praesentations-/Infrastruktur-Anliegen — Accept-Language ist ein HTTP-Protokollbelang (RFC 7231),
die Middleware ist Framework-gekoppelt, das Laden der Resource-Files ist Datei-IO. Nichts davon
gehoert in `shared_kernel`. Der `domain-purity`-Contract in `setup.cfg` erzwingt das inzwischen
maschinell fuer die Context-Domaenen.

**Einplanung: ganz ans Ende.** Nachweislich blockiert dieses Ticket **kein einziges** anderes
(`grep -l "Blocked by \[0008\]" docs/issues/*.md` liefert nichts). Fehlercodes wie
`email-already-registered` sind der API-Vertrag und sprachunabhaengig; lokalisierte `title`/`detail`
sind Kosmetik und koennen jederzeit nachgezogen werden.

## Acceptance criteria

Flach, ohne Stufengliederung: reine Praesentations-/Infrastruktur-Arbeit ohne eigene Fachregel,
siehe [`00-overview.md`](../milestones/00-overview.md), „Ticket-Schnitt".

- [ ] Derselbe Domaenenfehler liefert je nach Accept-Language-Header title/detail auf Deutsch oder Englisch
- [ ] Fehlt der Header, ist de-DE der Default
- [ ] Neue Fehlertexte werden zentral in den Resource-Files gepflegt, nicht inline im Code

## Blocked by

- Blocked by [0005](0005-m0-shared-kernel-rfc-7807-problemdetails-exception-handler.md)
