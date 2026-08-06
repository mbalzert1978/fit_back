---
schema_version: 1
name: fixture-die-none-liefert-ist-ein-ausschalter
description: Eine Fixture, die None liefert, damit die Tests durchlaufen, ist kein Test-Double, sondern ein Ausschalter - sie macht aus jedem darauf gebauten Test eine gruene Zeile ohne Aussage
type: feedback
frequency: 1
last_triggered: 2026-08-06
decay_eligible: false
---

Liefert eine Fixture `None`, damit ein Test ueberhaupt startet, und beginnt der
Test dann mit `if x is None: pytest.skip(...)`, dann prueft er **nichts** - und
sieht in jedem Lauf aus wie ein bestandener Test. Wo ein Testfall ohne echte
Ressource nichts pruefen kann, gehoert die echte Ressource her oder der Testfall
gestrichen.

**Why:** `tests/conftest.py` hatte eine `db_pool`-Fixture mit dem Kommentar „For
unit tests that don't need DB access, return None". Der eine Test, auf den es
bei einer Idempotenz-Middleware ankommt - zweiter Aufruf mit demselben
Schluessel liefert die gespeicherte Antwort -, uebersprang sich damit in jedem
Lauf selbst. Die verbleibenden Tests prueften ausschliesslich die
*Durchlass*-Faelle: kein Header, kein Nutzer, keine UUID. Also alles, was die
Middleware **nicht** tut.

Der Preis: drei Defekte blieben ueber Wochen unentdeckt, darunter ein
`json.loads(response.body)`, das mit `AttributeError` abgebrochen waere, sobald
der Speicherpfad je erreicht worden waere - er wurde nie erreicht. Aufgefallen
sind sie erst, als dieselben Tests gegen die Testcontainers-Engine liefen, die
es seit Ticket 0009 gibt. Vollstaendig in
[`docs/decisions/2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md`](../decisions/2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md).

**How to apply:** Diagnose-Signale beim Lesen einer Testdatei: eine Fixture mit
Rueckgabetyp `None`, ein `pytest.skip` mit einer Bedingung auf eine Fixture, ein
Kommentar der Form „ohne echte DB wird das uebersprungen". Jedes davon heisst:
diese Datei belegt weniger, als ihre Testnamen versprechen. Beim *Schreiben*: es
gibt keinen Grund mehr fuer eine Attrappen-Fixture, seit Testcontainers im Repo
steht - und wenn eine Ressource wirklich fehlt, ist ein fehlender Test ehrlicher
als ein uebersprungener. Verwandt:
[[gruenes-gate-ohne-scope-angabe]] (dasselbe Muster eine Ebene hoeher: gruen
heisst nicht geprueft), [[first-live-execution-surfaces-latent-bugs]].
