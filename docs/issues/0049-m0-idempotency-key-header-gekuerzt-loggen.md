---
id: "0049"
title: "M0: Ungueltigen Idempotency-Key gekuerzt loggen statt in voller Laenge"
status: open
milestone: M0
type: AFK
---

# M0: Ungueltigen Idempotency-Key gekuerzt loggen statt in voller Laenge

## What to build

`src/middleware/idempotency.py:253` schreibt einen ungueltigen `Idempotency-Key` ungekuerzt ins
Log:

```python
logger.warning(f"Invalid Idempotency-Key format: {idempotency_key_header}")
```

Der Wert kommt ungeprueft vom Aufrufer. Ein Client kann beliebig lange Header schicken, und jede
abgelehnte Anfrage schreibt den vollen Wert in die Logs — Log-Flooding, das nichts kostet ausser
einer HTTP-Anfrage. Der Header wird an dieser Stelle gerade deshalb geloggt, **weil** er ungueltig
ist; sein voller Wortlaut traegt zur Diagnose nichts bei, den die ersten Zeichen nicht auch
tragen.

Zu bauen: den geloggten Wert auf eine feste Laenge kuerzen (Vorschlag: 64 Zeichen, mit einer
Markierung, dass gekuerzt wurde) und die Laenge des Originals mitgeben, damit „viel zu lang" als
Ursache im Log sichtbar bleibt.

## Warum eigenes Ticket

Der Befund stammt aus dem Security-Gate von Ticket 0008, gehoert aber **nicht** dorthin: die Zeile
ist aelter, 0008 hat an `idempotency.py` nur die Uebersetzung der beiden ProblemDetails-Texte
angefasst. Ein Fix in jenem PR haette eine Aenderung eingeschmuggelt, die mit i18n nichts zu tun
hat.

## Umfang und Grenze

Klein und abgeschlossen — eine Logzeile plus ein Test, der belegt, dass ein ueberlanger Header
gekuerzt im Log landet.

Ausdruecklich **nicht** Teil dieses Tickets: eine allgemeine Laengenbegrenzung fuer Header oder
ein Rate-Limit auf der Middleware. Beides ist eine eigene Entscheidung an einer anderen Stelle der
Architektur.

## Definition of Done

- Der geloggte Wert ist auf eine feste Obergrenze gekuerzt und als gekuerzt erkennbar.
- Die Laenge des Originals steht im Log.
- Ein Test fuehrt einen ueberlangen `Idempotency-Key` und prueft die Logausgabe.
- Alle Gates gruen (ruff, format, import-linter, pytest, coverage_gap).
