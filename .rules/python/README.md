# Python Rules — Index

Alle Dateien sind sinngemaesse Uebersetzungen frueherer C#-Vorlagen (nicht mehr Teil dieses Repos)
fuer diesen Stack: **uv** + **ruff** (inkl. `ANN`-Regeln) + **ty** als Typechecker (Issue #97,
kein mypy/pyright), `requires-python = ">=3.14"`.

Empfohlene Lesereihenfolge fuer Neueinsteiger:innen: erst die Querschnittsregeln (1-6), dann die
Architektur-Klammer (7), dann die Spezialthemen (8-12).

| # | Datei | Thema |
|---|-------|-------|
| 1 | [python-code-organization.md](./python-code-organization.md) | Namen, Zustand vs. Verhalten, reine Funktionen |
| 2 | [python-types.md](./python-types.md) | Annotation, `@final`, `dataclass`, Tagged Unions |
| 3 | [python-modern-syntax.md](./python-modern-syntax.md) | f-Strings, Walrus, `uuid7`, PEP-695-Generics, noqa-Scoping |
| 4 | [python-control-flow.md](./python-control-flow.md) | `match`/`case`, Exhaustivitaet, Slicing, Literale |
| 5 | [python-null-safety.md](./python-null-safety.md) | Guards an public Grenzen, explizite Nullability |
| 6 | [python-error-handling.md](./python-error-handling.md) | `Result[T, E]`, Fehlernutzlast als typisierter Fall statt Satz, `parse`/`hydrate`, Fangen nur an der IO-Naht |
| 7 | [python-feature-slices.md](./python-feature-slices.md) | Drei-Schichten-Feature-Paket, Handler/Adapter/Mapper, Review-Checkliste |
| 8 | [python-rule-pattern.md](./python-rule-pattern.md) | Collect-all-`Rule` vs. Fail-fast-`ResultRule` |
| 9 | [python-factories.md](./python-factories.md) | Domaenen-benannte Factories, `hydrate`/`parse`, ein Wiring-Einstiegspunkt |
| 10 | [python-dependencies.md](./python-dependencies.md) | Schlanke Konstruktoren, `Protocol`-Komposition, Logging als Decorator |
| 11 | [python-data-access.md](./python-data-access.md) | Kein generisches Repository, Zeitpunkte als Value Object |
| 12 | [python-async.md](./python-async.md) | Kein Blockieren, native Cancellation, `TaskGroup`/`timeout` |

Bei Widersprueche zwischen zwei Dateien gilt die spezifischere: eine Aggregatwurzel-Regel in
feature-slices.md schlaegt die generische Zustand/Verhalten-Trennung aus
python-code-organization.md (dort explizit vermerkt).
