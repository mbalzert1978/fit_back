# QA-Gate: Coverage-Luecken scharf, Test-Facade-Check gestrichen

Die beiden Checks des `qa-check`-Skills lagen seit M0 abgeschaltet, mit der Bedingung im
eigenen `_note`: „reaktivieren, sobald M0/M1 die Paketstruktur etabliert haben". Mit den
gemergten Tickets 0010/0011 ist das eingetreten. Beim Nachsehen zeigte sich, dass
„wieder einschalten" fuer beide Checks etwas voellig Verschiedenes bedeutet.

## Was entschieden wurde

**`test_api_shape` ist ersatzlos gestrichen**, Skript geloescht. Das Skill
`slice-shape-check` stellt dieselbe Frage — traegt jedes Use-Case-Paket seine Test-API? —
passend zu diesem Layout, und zusaetzlich eine, die `test_api_shape` nie stellen konnte:
greift eine Spec an der Test-API vorbei in `domain`, `handler`, `mappers`, `fakes` oder
`infrastructure`? Es prueft `abstractions/`, `adapters/`, `mappers/`, `fakes/` und
`test_api/` als Ordner, ist diff-scoped und vollstaendig deterministisch. Zwei Skills
dieselbe Frage stellen zu lassen, davon eines kaputt, waere schlechter als eines.

**`coverage_gap` ist scharf geschaltet**, aber dafuer umgebaut. Das Flag auf `true` zu
setzen haette den Check nicht reaktiviert, sondern verschlimmert: das Skript suchte
Geschwisterprojekte im C#-Stil (`src/<Projekt>` neben `src/<Projekt>.Specs`), die es hier
nirgends gibt, und meldete deshalb fuer jeden Pfad `no-specs-sibling` und `gaps: 0` —
ein Gate, das dauerhaft sauber meldet und nie etwas findet.

Die Zuordnung Produktionseinheit → Testort ist jetzt nicht mehr verdrahtet, sondern eine
geordnete Regelliste in `config.json` (`coverage_rules`), jede Regel ein Glob plus ein
Template, in das dessen Platzhalter einsetzen. Erste passende Regel gewinnt, deshalb
speziell vor allgemein. Das bildet die zwei Test-Heimaten dieses Repos ab:

- `src/contexts/<ctx>/application/<use_case>/` → `src/contexts/<ctx>/specs/<use_case>/`
  (die Slice-Konvention aus `.rules/python/python-feature-slices.md`)
- alles uebrige spiegelt sich unter `tests/` — `src/api` → `tests/api`,
  `src/middleware` → `tests/middleware`, `src/infrastructure` → `tests/infrastructure`,
  `src/contexts/<ctx>` ausserhalb seiner Slices → `tests/contexts/<ctx>`

Einheiten schachteln sich, und ein geaenderter Pfad zaehlt zur **spezifischsten** Einheit,
die ihn enthaelt. Deshalb wird eine Slice-Aenderung an den Specs des Slice gemessen und
nicht zusaetzlich am Elternpaket — und ein reiner Container wie `src/contexts`, dessen
jede Aenderung einem Kind gehoert, erzeugt gar keine Zeile mehr.

Ein Testort kann in diesem Repo selbst unter `src/` liegen — die Slice-Specs tun das.
Solche Pfade werden verworfen, bevor irgendetwas zugeordnet wird; sonst meldete ein
Commit, der nur eine Spec anfasst, seinen eigenen Context als ungedeckte Luecke.

Zwei Ausgaenge sind neu und bewusst sichtbar statt still: `no-test-location`, wenn der
gemappte Testort gar nicht existiert, und `unmapped` fuer einen geaenderten `src/`-Pfad,
den keine Regel beansprucht. Beides heisst in aller Regel, dass `coverage_rules` vom
Layout abgedriftet ist — als schweigendes „sauber" durchzugehen waere genau der Fehler,
den der Umbau beseitigen sollte. Fehlt `coverage_rules` ganz, endet der Lauf mit
`Verdict: CONFIG ERROR` statt mit einem Pass, gemaess `_shared/validator-contract.md`.

## Warum das ueberhaupt aufgefallen ist

Weil beide Skripte tatsaechlich ausgefuehrt wurden, statt ihre Konfiguration zu lesen und
den Haken zu setzen. `test_api_shape` bricht mit `error: no feature projects found under
src matching prefix 'n/a'` und Exit 1 ab; `coverage_gap` lieferte neun Zeilen
`no-specs-sibling`. Dass ein umgebauter Check echte Luecken auch findet, ist ebenfalls
geprueft worden und nicht bloss angenommen: zwei Produktionsdateien testfrei angefasst,
Lauf meldet `gaps: 2`, Aenderungen zurueckgenommen.

## Was dadurch ersetzt wird

Der Eintrag in [`2026-08-05-0839-implementation-pipeline-and-wave-1.md`](2026-08-05-0839-implementation-pipeline-and-wave-1.md),
wonach beide Checks „laut eigenem `_note` deaktiviert bleiben", ist damit ueberholt. Das
Dokument selbst bleibt als datierter Beleg unveraendert.

Die Konfigurationsschluessel `specs_suffix`, `feature_project_prefix`,
`reference_feature_project`, `test_facade_glob` und `adr_reference` sind entfallen — sie
gehoerten alle zum gestrichenen Check.

## Nebenbefund: `fastapi.testclient` ist raus

`tests/api/test_exception_handlers.py` war die einzige Datei, die noch ueber
`fastapi.testclient.TestClient` an die App ging; alle anderen nutzen laengst
`httpx.ASGITransport` mit `AsyncClient`. Starlette 1.3 bindet den TestClient an `httpx2`
und warnt entsprechend bei jedem Lauf. Statt die Warnung zu filtern oder eine
Abhaengigkeit nachzuziehen, ist der eine Ausreisser auf das hauseigene Muster gezogen —
der TestClient ist ein Synchron-Wrapper mit eigenem Event-Loop, den der direkte
ASGI-Transport nicht braucht. Suite danach 152 gruen, ohne Warnungs-Sektion.
