# `pyjwt` hinter der Naht, Refresh-Token nur als Hash

**Datum:** 2026-08-21, 22:30
**Anlass:** [#95](https://github.com/mbalzert1978/fit_back/issues/95) stellt zum ersten Mal Tokens
aus. [`docs/milestones/01-technical-decisions.md`](../milestones/01-technical-decisions.md) hielt die
konkrete JWT-Bibliothek bis zum M1-Auth-Ticket offen; das ist dieses Ticket.

## 1. `pyjwt`, hinter einer Naht

Gewählt: `pyjwt`, HS256, mit `sub`/`iat`/`exp` als registrierten Claims. Der Algorithmus steht als
Konstante im Code und wird beim Prüfen (#52, #55) als erlaubte Liste übergeben, **nicht** aus dem
Header des Tokens gelesen — wer ihn von dort nimmt, lässt den Aufrufer ihn wählen, `none`
eingeschlossen.

Sie steckt hinter der Naht `RegisterUserSessionTokens`, genau wie `argon2-cffi` hinter
`RegisterUserPasswordHasher`: der Slice kennt Primitive, nicht das Verfahren. Ein selbst gebautes
HS256 wäre machbar gewesen, aber die Prüfseite — Algorithmus-Verwechslung, Ablauf, Leeway — ist der
Teil, an dem man sich schneidet, und sie kommt in #52 und #55 ohnehin.

**Das Geheimnis hat keinen Standardwert.** `JWT_SECRET` ist Pflicht und mindestens 32 Zeichen lang
(RFC 7518 Abschnitt 3.2; `pyjwt` warnt bei kürzeren nur, und eine Warnung im Log hält niemanden
auf). Ein Default wäre keine Bequemlichkeit, sondern eine Hintertür — dieser Fall steht schon einmal
in [2026-08-05-1130](2026-08-05-1130-security-gate-triage-ticket-0002-und-agent-integritaets-incident.md).

## 2. Ausstellen heißt ausstellen **und** ablegen

Die Naht hat eine Operation, `issue`, und die gibt den Refresh-Token zurück *und* legt ihn ab. Ein
herausgegebener Refresh-Token, den niemand einlösen kann, wäre eine Lüge, die das nächste Ticket
ausbaden müsste.

Abgelegt wird in `identity.refresh_tokens` über **dieselbe** Verbindung wie Nutzer-Zeile und
Outbox-Ereignis: entweder werden alle drei sichtbar oder keine. Ein Token zu einem Konto, das es
nicht gibt, ist damit kein möglicher Zustand.

**In der Datenbank steht nur der SHA-256-Hash.** Wer die Tabelle liest, könnte sich sonst als jeder
Nutzer ausgeben; zum Einlösen reicht der Hash, den Klartext bringt der Aufrufer mit. SHA-256 und
nicht Argon2id: der Token ist 256 Bit aus `secrets`, es gibt nichts zu erraten, wogegen ein
langsames Verfahren schützen müsste.

**Die Tabelle trägt nur, was #95 braucht** — `id`, `user_id`, `token_hash`, `issued_at`,
`expires_at`, mit `ON DELETE CASCADE` am Konto. Rotation und Reuse-Detection sind #53; ihre Spalten
entstehen dort, wo sie auch gelesen werden.

## 3. Wo die Sitzung entsteht

Als Schritt der Pipeline **nach** dem Handler und nur im Erfolgsfall (`bind_async`), nicht im
Handler selbst: der baut das Aggregat, und `User` weiß nichts von Tokens. Als Zeitpunkt dient
`registered_at` des Aggregats — dieselbe Uhrablesung, aus der auch die Nutzer-Zeile entsteht.

Die Lebensdauern (900 s / 5 184 000 s, `BACKEND.md` Abschnitt 8) kommen mit der ausgestellten
Sitzung heraus, statt am HTTP-Rand ein zweites Mal als Konstante zu stehen.

## Was dadurch ausgeschlossen wird

- Keine handgeschriebene JWT-Signatur oder -Prüfung.
- Kein Algorithmus aus dem Token-Header.
- Kein Klartext-Refresh-Token in der Datenbank.
- Keine Token-Ausstellung im Handler oder am HTTP-Rand.
- Keine Rotationsspalten auf Vorrat.
