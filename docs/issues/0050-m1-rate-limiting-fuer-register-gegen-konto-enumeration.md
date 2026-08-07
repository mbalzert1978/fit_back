---
id: "0050"
title: "M1: Rate-Limiting fuer POST /register gegen Konto-Enumeration"
status: open
milestone: M1
type: AFK
---

# M1: Rate-Limiting fuer `POST /register` gegen Konto-Enumeration

## What to build

`POST /register` beantwortet eine bereits vergebene E-Mail mit HTTP 409 und dem Code
`email-already-registered`. Wer die Antwort systematisch fuer viele Adressen abfragt, kann
feststellen, welche davon ein Konto haben — Konto-Enumeration.

Zu bauen: eine Begrenzung der Versuchsrate auf diesem Endpunkt, sodass das Abklappern einer Liste
teuer wird, waehrend eine echte Registrierung unbehelligt bleibt.

## Warum das der richtige Ort ist — und nicht die Fehlermeldung

Das Security-Gate von 0008 hat diesen Punkt als Leck in der Fehlermeldung gemeldet, mit dem
Vorschlag, die E-Mail-Adresse aus dem Antworttext zu nehmen. Das ist der falsche Hebel, aus zwei
Gruenden:

1. **Die Antwort verraet nichts Neues.** Die gespiegelte Adresse ist die, die der Aufrufer im
   selben Request gerade selbst geschickt hat. Sie zu entfernen kostet dem Angreifer nichts — der
   Statuscode allein traegt die Information bereits.
2. **Die Unterscheidung ist die Funktion.** Ein Registrier-Endpunkt, der eine vergebene Adresse
   nicht als vergeben meldet, kann seine Aufgabe nicht erfuellen. Wer sich anmelden will, muss
   erfahren, dass er es schon getan hat. Die Enumeration ist damit keine Panne der Formulierung,
   sondern die Kehrseite einer notwendigen Zusage.

Was die Domaene bereits richtig macht: `EmailAlreadyRegistered`
(`src/contexts/identity/domain/errors.py:36-46`) traegt bewusst **nicht**, *wem* die Adresse
gehoert. Verraten wird also die Existenz eines Kontos, nie seine Identitaet.

Bleibt der Hebel, der wirklich greift: die Rate. Deshalb dieses Ticket.

## Offene Entscheidungen fuer die Umsetzung

Vor der Implementierung zu klaeren und unter `docs/decisions/` festzuhalten:

- **Bezugsgroesse** — pro IP, pro Adressbereich, oder pro Kombination aus beidem? Reines IP-Limit
  trifft Nutzer hinter einem gemeinsamen NAT mit.
- **Ablage der Zaehler** — in Postgres (ein Backend weniger) oder in einem eigenen Speicher? Der
  Stack hat bislang kein Redis, und dieses Ticket ist kein Anlass, eines einzufuehren.
- **Antwort bei Ueberschreitung** — HTTP 429 mit `Retry-After`, als ProblemDetails im Format der
  uebrigen Fehler und mit eigenem Code, der wie alle anderen aus einer Tagged Union abgeleitet und
  vom Startup-Check erfasst wird
  ([`2026-08-07-0805`](../decisions/2026-08-07-0805-fehlercodes-werden-abgeleitet-nicht-gepflegt.md)).
- **Reichweite** — nur `/register`, oder gleich eine Middleware fuer alle schreibenden Endpunkte?
  `.rules/common/security.md` verlangt „Rate limiting on all endpoints"; dieses Ticket ist die
  Gelegenheit, das Muster einmal richtig zu setzen, statt es je Endpunkt nachzuziehen.

## Definition of Done

- `POST /register` ist ratenbegrenzt; das Ueberschreiten liefert 429 mit `Retry-After`.
- Der Fehlercode stammt aus einer Tagged Union und ist in `ERROR_UNIONS` (`src/main.py`)
  eingetragen — nicht in `PRESENTATION_CODES`.
- Texte liegen in beiden Sprachdateien; der Startup-Drift-Check laeuft durch.
- Ein Test belegt, dass wiederholte Versuche begrenzt werden und eine einzelne Registrierung nicht.
- Die getroffenen Entscheidungen liegen unter `docs/decisions/`.
- Alle Gates gruen.
