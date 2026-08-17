---
schema_version: 1
name: gh-api-paginate-schneidet-still-ab
description: gh api liefert ohne --paginate nur die ersten 30 Eintraege und sagt es nicht - eine Frontier-Abfrage ueber Sub-Issues meldet dann zu wenige Tickets statt eines Fehlers
type: feedback
frequency: 1
last_triggered: 2026-08-17
decay_eligible: false
---

Jede `gh api`-Abfrage auf eine **Liste** bekommt `--paginate`. Ohne es liefert GitHub die erste
Seite — standardmaessig 30 Eintraege — und weist mit keinem Zeichen darauf hin, dass mehr da ist.
Kein Fehler, kein Hinweis, keine abweichende Struktur; nur ein zu kurzes Ergebnis, das aussieht
wie ein vollstaendiges.

Konkreter Fallstrick: Die Frontier-Abfrage der Wayfinder-Map #40 (50 Kinder) meldete **ein**
offenes, unblockiertes Ticket statt fuenf, weil `.[] | select(...)` nur ueber die ersten 30
Kinder lief. Das Ergebnis war plausibel — genau das macht es gefaehrlich: „eine Frontier" ist
ein voellig normaler Zustand einer Map, also gibt es nichts, woran der Fehler auffiele.

Zu beachten: `--paginate` haengt bei mehreren Seiten **je ein JSON-Array pro Seite** aneinander.
Wer die Ausgabe in Python o. ae. weiterverarbeitet, kann sie nicht mit einem `json.loads()`
lesen, sondern muss die Arrays mit `JSONDecoder().raw_decode()` in einer Schleife einsammeln.
Mit `--jq` stellt sich die Frage nicht, das arbeitet ohnehin stromweise.

**Why:** Die Abfrage stand woertlich so in `docs/agents/issue-tracker.md` und war damit die
kanonische, kopierbare Form fuer jede Wayfinder-Sitzung in diesem Repo. Solange die Map unter 30
Kindern blieb, war sie korrekt; ab dem 31. Kind verschwieg sie still Tickets — inklusive der
Moeglichkeit, dass eine Sitzung „keine Frontier, alles blockiert" gemeldet und die Map fuer
erledigt gehalten haette. Aufgefallen ist es nur, weil das Ergebnis (`#51`) gegen eine vorher
von Hand erstellte Liste (`#51, #71, #86, #89, #90`) gehalten wurde.

**How to apply:** `--paginate` als Standard behandeln, nicht als Optimierung — die Auslassung ist
die Ausnahme, die begruendet werden muss, nicht umgekehrt. Bei jeder Listenabfrage, deren Laenge
in eine Entscheidung eingeht, einmal `--jq 'length'` gegen `--paginate ... | wc -l` halten; sind
es exakt 30 (oder 100), ist das kein Zufall, sondern die Seitengrenze. Dieselbe Logik wie
[[pruefkommando-muss-messen-was-es-behauptet]]: ein zu kurzes Ergebnis beweist so wenig wie ein
leeres, solange nicht gezeigt ist, dass die Abfrage ueberhaupt alles sehen kann. Verwandt:
[[gruenes-gate-ohne-scope-angabe]].
