# Slice-Form verbindlich geklaert: Context-Schnitt, Test-API, Naht-Besitz, Baureihenfolge

## Kontext

Nach zwei Wellen (M0, Tickets 0001-0010) hatte **jeder** PR dieselbe Klasse Verstoesse:
Abhaengigkeitsrichtung invertiert, `shared_kernel` mit `starlette`/`fastapi`/`pydantic`/`asyncpg`
verunreinigt, kein Pattern Matching, Exceptions statt `Result`, Tests am falschen Ort. Das interne
QA-Gate hat trotzdem `APPROVE` erteilt (Ursache und Gegenmassnahme dazu:
[2026-08-06-0702-qa-gate-haerten-struktur-review.md](2026-08-06-0702-qa-gate-haerten-struktur-review.md)).

Bei der Ursachensuche zeigte sich ein zweiter, tieferer Grund: **die Slice-Form war nie
vollstaendig festgeschrieben.** `.rules/python/python-feature-slices.md` beschrieb Schichten,
`Result[T, E]`, VOs und Rollentrennung sauber — aber die zentralen Bausteine fehlten oder standen
nur in einer Nebensatz-Zeile. Es existiert ausserdem **kein einziges implementiertes Feature-Slice**
in diesem Repo (M0 hat ausschliesslich Infrastruktur gebaut), und
`.claude/skills/review-against-rules/config.json` vermerkt selbst, dass deshalb keine
Referenzimplementierung konfiguriert ist. Jeder Agent hat die Form also **jedes Mal neu erfunden**.

Als Vorlage dient das Schwesterprojekt `C:\temp\apps\dhcp-mac-verwaltung` (C#), aus dem die
`.rules/`-Dateien sinngemaess uebersetzt wurden — insbesondere dessen `Features.MacSuche`-Slice und
die zugehoerigen ADRs 0003/0006/0007/0008/0009.

## Entscheidung

Sieben Fragen wurden vom Stakeholder verbindlich beantwortet:

1. **Context-Schnitt.** Ein Bounded Context ist die Feature-Paket-Grenze: **eine** `domain/`-Schicht,
   darunter **je Use Case ein `application/<use_case>/`**. Der `Result`-Fehlertyp ist damit
   **context-eigen**, nicht use-case-eigen.
2. **Test-API-Granularitaet.** **Je Use Case eine Test-API.**
3. **Naht-Besitz.** Die **Domaene gibt die Ports vor**, die sie braucht; der **Use Case adaptiert**
   sie und formuliert daraus seine **eigene, schmale public Anforderung**. Kein geteiltes Gateway —
   auch nicht fuer Persistenz.
4. **Naht-Ergebnis.** Die public Seite liefert eine **eigene, einfache Tagged Union**;
   `Result[T, E]` bleibt **domaenenseitig** und kreuzt die public Naht nie.
5. **Testcontainers.** Testcontainers-basierte Tests sind **End-to-End** und **nicht Teil der
   Test-API**. Die Test-API testet den Slice gegen **einfache In-Memory-Fakes**.
6. **Reihenfolge des Aufraeumens.** Zuerst `register_user` (Ticket 0011) als **erstes echtes Slice
   und Referenzimplementierung**. Was in den `shared_kernel` wandert, wird **beim zweiten Slice**
   entschieden — `Result` auf jeden Fall.
7. **Baureihenfolge im Slice.** Von der Domaene nach aussen; Infrastruktur zuletzt. Ein Slice ist
   **fertig und abnehmbar, bevor Infrastruktur existiert.**

## Konsequenzen

**`.rules/python/python-feature-slices.md` erweitert** um die bisher fehlenden Bausteine:

- Bounded-Context-Schnitt (eine `domain/`, je Use Case ein `application/<use_case>/`).
- Abschnitt „Die Naht gehoert dem Use Case — kein geteiltes Gateway": drei Regeln (nur benoetigte
  Operationen, nur Primitive ueber der Naht, eigene Tagged Union statt `Result`), mit Do/Don't.
- Abschnitt „Die Test-API ist Teil des Slice, nicht des Testprojekts": Ablage
  (`application/<use_case>/test_api.py`, Fakes unter `application/<use_case>/fakes/`),
  Arrange/Act/Assert-Tabelle, Beispiel, Abgrenzung zu Integrations-/E2E-Tests.
- Abschnitt „Baureihenfolge: Domaene zuerst, Infrastruktur zuletzt" — fuenf Stufen, mit der
  expliziten Feststellung: ein Ticket, das nur Infrastruktur oder nur den HTTP-Router liefert, ist
  kein Tracer Bullet.
- Review-Checkliste um zehn Punkte erweitert.

**Ticket 0011 (`register_user`) wird zur Referenzimplementierung.** Sobald es gemergt ist, zeigt
`.claude/skills/review-against-rules/config.json` per `reference_implementation` darauf — damit
entfaellt das Erfinden der Form je Agent, was die eigentliche strukturelle Ursache war.

**Der `shared_kernel`-Neuschnitt** (aktuell mit `starlette`/`fastapi`/`pydantic`/`asyncpg`
verunreinigt, stammend aus den gemergten Tickets 0005/0006/0007) wird **nicht vorgezogen**, sondern
nach dem zweiten Slice entschieden — dann liegt belastbare Evidenz vor, was wirklich geteilt gehoert.
Bis dahin bleibt er als bekannte Altlast dokumentiert.

## Offen

- Ein import-linter-Contract, der `shared_kernel` gegen externe Pakete absichert, existiert **nicht**
  (`.importlinter` deckt nur die Context-Grenzen ab). Er kann erst scharf gestellt werden, wenn der
  `shared_kernel` sauber ist — bis dahin bleibt die Regel unerzwungen.
