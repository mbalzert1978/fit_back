# Idempotenz: erst reservieren, dann arbeiten

**Entschieden:** 2026-08-06, 17:30 — aus der Gate-Triage vor dem PR zu Ticket 0010/0011.

## Der Anlass

Fünf Gates liefen gegen den Branch. Drei von ihnen haben `src/middleware/idempotency.py`
angesehen und je einen Teil davon ausdrücklich als in Ordnung abgehakt — das Security-Gate sogar
mit „Benutzer-Isolation via `user_id` + `request_hash`" ✓. Tatsächlich hatte das Modul **drei
Defekte**, und keiner der Berichte hatte mehr als einen davon:

1. **Der `request_hash` wurde berechnet, gespeichert — und nie verglichen.** Derselbe Schlüssel
   mit einem anderen Body lieferte die Antwort der ersten Anfrage. Der Client hielt seinen
   zweiten, völlig anderen Vorgang für erledigt. Genau dafür steht die Spalte in
   `docs/Draft/BACKEND.md`, Abschnitt 0.3, überhaupt in der Tabelle.
2. **`SELECT` vor `INSERT`.** Zwei gleichzeitige Anfragen mit demselben Schlüssel liefen beide an
   der Abfrage vorbei, führten beide den Vorgang aus, und die zweite Einfügung brach am
   Unique-Index — der Fehler wurde geloggt und geschluckt. Das ist das Muster, gegen das dieses
   Repo eine eigene Regel hat
   ([`exp_keine-vorpruefung-wo-die-gegenseite-entscheidet`](../reflections/exp_keine-vorpruefung-wo-die-gegenseite-entscheidet.md)).
3. **`request.state.user_id` setzt niemand.** Die JWT-Pipeline ist Ticket 0012. Bis dahin
   überspringt die Middleware jede Anfrage.

Punkt 3 erklärt 1 und 2: **die Middleware hat noch nie etwas getan.** Ein Modul ohne Ausführung
sammelt Fehler an, die niemand bemerkt — dieselbe Ursache wie beim nicht importierbaren
`main.py` ([`2026-08-06-1245`](2026-08-06-1245-main-py-war-nicht-importierbar.md)) und beim
abgebrochenen Startup ([`2026-08-06-1500`](2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md)).

## Die Entscheidung

**Die Zeile entsteht, bevor die Anfrage verarbeitet wird**, als Reservierung mit
`response_body IS NULL`. Wer zuerst schreibt, hat den Schlüssel — das entscheidet der
Unique-Index in einem Statement (`ON CONFLICT DO NOTHING RETURNING`), nicht eine vorgelagerte
Abfrage. Zwischen Frage und Antwort passt keine zweite Anfrage mehr, weil es die Frage nicht mehr
gibt.

Scheitert die Reservierung, ist der Schlüssel vergeben, und es gibt genau vier Ausgänge:

| Zustand der bestehenden Zeile | Antwort |
|---|---|
| gleicher Nutzer, gleicher Body, Antwort liegt vor | die gespeicherte Antwort, mit `200` |
| gleicher Nutzer, gleicher Body, Antwort steht aus | `409` — die erste Anfrage läuft noch |
| gleicher Nutzer, **anderer** Body | `422` — derselbe Schlüssel für etwas anderes |
| **anderer** Nutzer | `422` — identisch zum Fall darüber |

Die letzten beiden Fälle geben bewusst **dieselbe** Antwort. Wären sie unterscheidbar, ließe sich
damit abtasten, welche Schlüssel fremde Nutzer vergeben haben.

Die Statuscodes folgen dem IETF-Entwurf zum `Idempotency-Key`-Header. `BACKEND.md` schreibt nur
den Treffer-Fall (`200`) vor und sagt zu den übrigen nichts.

**Eine Reservierung ohne wiederholbare Antwort wird freigegeben** — bei einem Fehlerstatus wie
bei einer geworfenen Ausnahme. Sonst verbrennte ein einziger Fehlschlag den Schlüssel dauerhaft,
und der Client könnte den Vorgang nie erneut versuchen.

Dafür wird `response_body` nullable (`shared_004`): NULL heißt „belegt, Antwort steht aus". Unter
der alten Regel ließ sich dieser Zustand nicht abbilden — es gab die Zeile erst, wenn es auch
schon eine Antwort gab, und genau in dieser Lücke lief die zweite Anfrage durch.

## Was das über die Gates sagt

Der Fund stammt nicht aus einem Gate-Bericht, sondern aus dem Nachprüfen der Berichte. Beide
`BLOCK`-Urteile hielten der Prüfung nicht stand: Das Security-Gate wollte den `409` bei vergebener
E-Mail entfernen, den `BACKEND.md` Zeile 124 wörtlich vorschreibt; das Design-Gate wollte den
`200` beim Treffer ändern, den Abschnitt 0.3 wörtlich vorschreibt. Beide Male sollte eine
Spezifikationsentscheidung einem allgemeinen Prinzip weichen.

Umgekehrt stand im Standards-Bericht „Keine echten Zweifelsfälle" — und im selben Bericht
„keine Vorprüfung ✓", geprüft am `PostgresUserStore`, während die Middleware daneben genau das
tat. Das bestätigt zwei bestehende Reflections auf einmal:
[`exp_review-agent-null-findings-ist-kein-freibrief`](../reflections/exp_review-agent-null-findings-ist-kein-freibrief.md)
und [`exp_zweifelsfaelle-bericht-deckt-regel-luecken-auf`](../reflections/exp_zweifelsfaelle-bericht-deckt-regel-luecken-auf.md).

**Ein Gate-Bericht ist ein Rohbefund, kein Urteil.** Er wird gegen die Spezifikation geprüft,
bevor er etwas auslöst — und was er als „✓ geprüft" führt, ist die Stelle, an der am ehesten
nachzusehen ist.

## Was das ausschließt

- Kein `SELECT`, das fragt, was ein `INSERT` ohnehin entscheidet — auch nicht „nur zum Nachsehen".
- Keine gespeicherte Antwort ohne Vergleich des `request_hash`.
- Kein Modul mehr, dessen Weg ausschließlich durch Tests belegt ist, ohne dass das im Docstring
  steht. Für diese Middleware steht es dort, samt Ticket 0012 als Bedingung.
