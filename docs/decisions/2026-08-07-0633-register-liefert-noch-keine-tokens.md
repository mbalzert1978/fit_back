# POST /register liefert noch keine Tokens — die Token-Rueckgabe gehoert zu 0012

**Datum:** 2026-08-07, 06:33

## Problem

Ticket 0011 (Stufe 3) forderte, dass `POST /api/v1/identity/register` mit `201` und
`userId/accessToken/refreshToken/expiresInSeconds` antwortet — so auch `docs/Draft/BACKEND.md:123`.
Die Token-Ausstellung selbst ist aber Ticket **0012** (JWT-Auth-Pipeline), und 0012 traegt
`Blocked by 0011`. Damit war keines der beiden Tickets zuerst abschliessbar: ein **Zyklus** im
Abhaengigkeitsgraphen.

Dasselbe Muster traf das Idempotenz-Kriterium aus 0011: die Middleware
(`src/middleware/idempotency.py:257-259`) steigt ohne `request.state.user_id` bewusst aus, und
diesen Wert setzt erst die Auth-Middleware aus 0012.

Die Umsetzung wich bereits still ab — der gemergte Endpunkt liefert ein Profil-Objekt ohne Tokens.

## Entscheidung

**Das Token-Kriterium wird aus 0011 herausgeloest und nach 0012 verschoben.** 0011 Stufe 3 liefert
`201` mit dem angelegten Konto (`userId`, `email`, `displayName`, `locale`, `timeZoneId`,
`registeredAt`) und **keinen** Tokens. 0012 ruestet den Register-Endpunkt um die Token-Felder nach,
sobald es die Ausstellung gebaut hat, und traegt dafuer ein eigenes Akzeptanzkriterium.

Ebenso wandert der Idempotenz-Nachweis fuer `/register` nach 0012: 0011 belegt nur noch, dass der
Endpunkt hinter der Middleware haengt, nicht, dass ein zweiter Aufruf `200` liefert.

`docs/Draft/BACKEND.md:123` bleibt fachlich gueltig — es beschreibt den **Endzustand** des
Endpunkts, nicht die Reihenfolge, in der er entsteht.

## Warum nicht 0012 aufteilen

Die Alternative waere gewesen, ein neues Ticket nur fuer die reine Token-Ausstellung vor 0011
Stufe 3 zu ziehen. Dagegen sprach: 0011 ist bis auf drei Restpunkte fertig und gemergt, der Zyklus
haette es kuenstlich laenger offen gehalten; und die Auth-Middleware, die das Idempotenz-Kriterium
braucht, waere trotzdem erst mit 0012 gekommen — der Zyklus waere also nur halb aufgeloest worden.

## Folgen

- 0011 kann geschlossen werden, sobald der Contract-Test steht; der Zyklus zu 0012 ist weg.
- 0012 waechst um zwei Kriterien (Token-Nachruestung an `/register`, Idempotenz-Nachweis dort).
- Die abweichende Antwortform des Endpunkts ist ab jetzt ein **dokumentiertes Provisorium**, kein
  stiller Bug.
