# Ein wiederverwendeter Idempotency-Key antwortet mit 409, und ein anonymer Aufruf belegt ihn

**Datum:** 2026-08-22, 15:00
**Anlass:** Die neue Fassung des Frontend-Pacts
(`contracts/pacts/identity/nutritrack-app-nutritrack-identity.json`, 26 statt 11 Interaktionen)
brachte die Interaktion „Registrierung unter einem schon vergebenen Schlüssel" mit. Sie kollidiert
an zwei Stellen mit `src/middleware/idempotency.py`. Beides hatte
[#95](https://github.com/mbalzert1978/fit_back/issues/95) unter „Zu prüfen, nicht vorentschieden"
offen gelassen; der Vertrag entscheidet es jetzt.

## 1. Der Statuscode: 422 → 409

Der Vertrag verlangt für den wiederverwendeten Schlüssel **409** mit
`tag:nutritrack.app,2026:problems/idempotency-key-reused` — ohne Matcher, also bindend. Die
Middleware antwortete dafür **422**.

Die alte Wahl war begründet, nicht beliebig: der Modul-Docstring leitete sie aus dem IETF-Entwurf
zum `Idempotency-Key`-Header ab. Aber ein Entwurf ist ein Entwurf, und der Pact ist die Vorgabe der
HTTP-Grenze ([`2026-08-21-1330`](2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md),
Punkt 1: „Wo beides kollidiert, gewinnt der Vertrag, und die Invariante wird nachgezogen").

Fachlich verliert dabei nichts: der Schlüssel steht im Konflikt mit einem bestehenden Zustand, der
Rumpf selbst ist verarbeitbar — das ist die Lesart von 409, nicht die von 422.

**Damit antworten drei der vier Ausgänge mit 409.** Unterscheidbar bleiben sie am `type`:
`request-in-progress` für den noch laufenden Erstversuch, `idempotency-key-reused` für den belegten
Schlüssel. Der Statuscode war nie das Unterscheidungsmerkmal — der Bezeichner ist es.

Die Umstellung berührt eine Middleware, die für den **ganzen Host** gilt, nicht nur für
`/register`. Sie ist trotzdem hier gemacht und nicht als eigenes Ticket geparkt: die Interaktion
lässt sich anders nicht grün bekommen, und ein Ticket, das den Statuscode später noch einmal
anfasst, änderte nur, wann derselbe Schnitt passiert.

## 2. Ein Aufruf ohne Anmeldung belegt seinen Schlüssel trotzdem

Die Middleware stieg bisher ohne `request.state.user_id` aus („No user_id in request state,
skipping idempotency check"). Bei der Registrierung gibt es keinen angemeldeten Nutzer — die
Middleware lief an dieser Route also gar nicht, und die Interaktion konnte nie eine Antwort
bekommen.

**Entschieden:** Fehlt die `user_id`, tritt `ANONYMOUS_USER_ID` (die Nil-UUID) an ihre Stelle.

- **Die Nil-UUID und kein `NULL` in der Spalte.** `user_id` ist `NOT NULL`, und ein `NULL`
  verglichen sich nach SQL-Regeln mit nichts — auch nicht mit sich selbst. Ein fester Wert hält den
  Vergleich in `_answer_from_existing` genau so, wie er für angemeldete Nutzer schon funktioniert.
  Keine Migration nötig.
- **Unter dem Ersatz-Nutzer entscheidet allein der `request_hash`**, ob hinter dem Schlüssel
  dieselbe Anfrage steckt. Genau so ist es vor der Anmeldung gemeint: wer der Aufrufer ist, weiß
  vor ihr niemand.
- Fachlich ist das kein Notbehelf. Die Registrierung braucht die Idempotenz **gerade dort** am
  dringendsten: zweimal abgeschickt entstünde sonst ein zweites Konto.

Die Idempotenz-Logik selbst — Reservieren-dann-arbeiten, `ON CONFLICT DO NOTHING RETURNING`, der
Hash-Vergleich — bleibt unangetastet.

## Was dadurch ausgeschlossen wird

- Kein 422 mehr für einen wiederverwendeten oder fremden Idempotency-Key.
- Keine Route mehr, an der die Middleware wegen fehlender Anmeldung stillschweigend aussetzt; der
  einzig verbliebene Ausstieg ist die fehlende Datenbank-Engine.
- Keine Unterscheidung der beiden Wiederverwendungs-Fälle (fremder Nutzer vs. abweichender Rumpf)
  nach außen — sie bleiben absichtlich ununterscheidbar, sonst ließe sich damit die
  Schlüsselvergabe fremder Nutzer abtasten.
