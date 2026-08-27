# Der Review-Durchgang: eine Fabrik, ein Wächter für die Sperre, eine konfigurierbare API-Version

## Was entschieden wurde

Ein Zwei-Achsen-Review des Branches `fix/openapi-dokument-ohne-umschlag` gegen `main` hat neun
Befunde geliefert. Was daraus folgte, steht hier — die Befunde selbst sind erledigt und nicht
festhaltenswert.

## 1. Kein Docstring erklärt mehr den Entwurf

Der Docstring des Endpunkts `POST /api/v1/identity/register` landete wörtlich als `description` im
veröffentlichten OpenAPI-Dokument — samt Verweis auf `.rules/python/python-error-handling.md`. Eine
interne Entwurfsbegründung im Frontend-Vertrag, ausgerechnet in dem Branch, der die veröffentlichte
Beschreibung geradezieht.

Die veröffentlichte Beschreibung lautet jetzt „Lege ein Konto an." und sonst nichts. Dieselbe
Streichung lief über `user.py`, `i18n.py`, `register_user_response.py`, `register_user_problem.py`
und `construction.py`: Entwurfsbegründungen, die in `docs/decisions/` schon stehen, sind auf einen
Verweis eingedampft. Stehen geblieben ist, was die Signatur nicht sagt — Vorbedingungen,
Reihenfolgen, Fälle, in denen etwas *nicht* passiert.

Der Docstring von `RegisterUserCommand` war seit
[2026-08-26-2330](2026-08-26-2330-die-wurzel-sammelt-ihre-befunde-selbst.md) schlicht falsch: er
beschrieb die abgeschaffte Doppelprüfung. Der Streichtest-Durchgang von
[2026-08-27-1030](2026-08-27-1030-docstrings-bestehen-den-streichtest.md) hatte ihn übersehen.

## 2. `UserFactory` statt `User.create`

`User.create` trug acht Parameter — fünf Rohwerte und drei Ports — und brauchte dafür ein
`# noqa: PLR0913`. Die drei Ports reisten immer zusammen: ein Data Clump.

Die Ports sitzen jetzt auf einer Fabrik:

```python
@final
@dataclass(frozen=True, slots=True)
class UserFactory:
    idn: IdnEncoder
    hasher: PasswordHasher
    clock: TimeProvider

    def create(self, *, email, password, display_name, locale, time_zone) -> AsyncResult[User, UserRejected]:
```

Sie sind Mitarbeiter der Fabrik, nicht Eingabe eines einzelnen Aufrufs
([`python-factories.md`](../../.rules/python/python-factories.md)). Das `noqa` fällt weg.

Der Handler schrumpft mit: statt fünf Konstruktor-Parametern nimmt er drei (`users`, `registry`,
`events`) und reicht keine Ports mehr durch. Verdrahtet wird die Fabrik in `pipeline.py`, der einen
Stelle, an der der Slice zusammengesteckt wird.

Die verschachtelte Tupelform der `zip_all`-Kette (`((((a, b), c), d), e)`) verlässt `create` nicht
mehr: die Kette endet auf `.map(_checked)` in ein benanntes `_CheckedFields` mit fünf Feldern. Die
eine Entpackung steht in `_checked`; `_assembled` liest `fields.email` statt einer Position.

Die fünf gleichgeformten `*_rejection`-Einzeiler sind ein generischer Lifter geworden:
`rejection(EmailRejected)`. Der Fall steht damit an der Aufrufstelle statt in einem Namen daneben.

## 3. Die Konstruktor-Sperre bekommt einen Wächter

[2026-08-26-2030](2026-08-26-2030-die-wurzel-haelt-ihre-invarianten-selbst.md) sagte „**jedes** Value
Object des Identity-Context hält ein modul-privates `ConstructionKey`". Umgesetzt war es in sechs von
acht Modulen. Die Sperre besteht je Typ aus drei Teilen — `_KEY`, dem `key`-Feld und dem
`deny_foreign_key` — und ein vergessener Teil fällt zur Laufzeit nirgends auf.

Weder Basisklasse noch Protocol lösen das. Eine Basisklasse scheitert praktisch an
`@dataclass(frozen=True, slots=True)`: das geerbte Feld legt seinen Slot ein zweites Mal an. Ein
Protocol beschreibt nur die Form und hält zur Laufzeit niemanden auf — die Sperre ist aber genau eine
Laufzeit-Sperre.

Stattdessen ein Architektur-Test,
[`test_architecture_construction_key.py`](../../tests/test_architecture_construction_key.py), nach
dem Muster des schon bestehenden `test_architecture_datetime.py`. Die Regel ist der **Rohwert**: ein
Typ mit einem primitiven Feld hält eine Regel, die niemand geprüft hat, und braucht die Sperre.
Geprüft wird jedes `value_objects/` jedes Contexts, nicht ein fester Pfad.

Damit ist auch die Ausnahme benannt und nicht länger ein Loch: eine Tagged Union ohne Feld (`German`,
`Active`) hat keinen Rohwert; `PendingDeletion` trägt einen `Timestamp`, also einen bereits geprüften
Typ. Der Docstring von `ConstructionKey` sagt das jetzt so.

### Die gemeinsamen Bausteine der Architektur-Tests

Beide Tests stehen auf [`tests/architecture_ast.py`](../../tests/architecture_ast.py): `Befund`,
`modules(keep)`, `no_findings(...)`. Der erste Wurf des neuen Tests hatte alle drei nachgebaut, dazu
die Zeilennummer verloren und die Struktur mit `isinstance`-Ketten abgetastet — genau die Form, die
[`python-control-flow.md`](../../.rules/python/python-control-flow.md) als *Don't* führt, mit
`test_architecture_datetime.py` als Quelle des *Do*.

Eine Falle dabei: ein nackter Name in einem `case`-Pattern ist ein Capture, kein Vergleich.
`case ast.Name(id=_GUARD)` hätte auf alles gepasst. Die Literale stehen deshalb direkt im Pattern.

## 4. `Cache-Control` gilt jetzt wirklich für jede Antwort

Der Nachtrag an der Beschreibung trug an *jede* Antwort „Immer `no-store`" ein. Die
Umschlag-Middleware setzte den Header aber nur im eingepackten Zweig; eine 204 oder eine
Nicht-JSON-Erfolgsantwort bekam ihn nie. Latent, weil es heute nur `/health` und `/register` gibt —
aber genau die Drift, gegen die [2026-08-26-1700](2026-08-26-1700-die-beschreibung-holt-die-middleware-ein.md)
antritt.

Beide Zweige setzen ihn jetzt.

## 5. Die API-Version steht in den Settings — mit eigenem Weg herein

Dasselbe Decision-Doc versprach, der Nachtrag trage vier Dinge ein, darunter `info.version`.
Tatsächlich stand die Version nur an `FastAPI(version=...)` in `src/main.py`. Eine zweite App, die
`document_middleware_effects` aufruft und `version=` vergisst, bekam still `0.1.0`.

Der Nachtrag setzt `info.version` jetzt selbst und nimmt sie als Parameter. Der Wert kommt aus den
Settings: `Settings.api_version`, Default `DEFAULT_API_VERSION`, überschreibbar über `API_VERSION`.
Die Middleware bekommt ihn im Konstruktor statt aus einer Modulkonstante
([2026-08-07-0750](2026-08-07-0750-ressourcen-per-dependency-injection-statt-modulglobal.md)).

**Der eigene Weg herein.** `get_api_version()` steht neben `get_settings()` und nicht darin.
`src/main.py` verdrahtet Middleware und Nachtrag beim **Import**, und dort darf noch keine
vollständige Umgebung nötig sein — `tests/api/test_app_startup.py` hält das ausdrücklich fest:

> `from src import main` darf keine Umgebungsvariablen und keine Datenbank brauchen.

`get_settings()` scheitert ohne `DB_PASSWORD` und `JWT_SECRET`. Die API-Version ist die einzige
Angabe mit einem Default und braucht die anderen nicht. `get_settings()` liest sie über denselben
`get_api_version()`, damit beide Wege nicht auseinanderlaufen können.

Der Test dazu prüft jetzt den Nachtrag statt sich selbst: die Test-App in `_document()` übergibt
`FastAPI()` **ohne** `version=`. Trägt der Nachtrag sie nicht ein, steht dort `0.1.0`.

## Was nicht entschieden wurde

- **`_settled` kommt nicht zurück.** `AsyncResult(_ready(self))` steht an fünf Stellen. Eine
  Hilfsfunktion darum wäre eine reine Durchreiche und spart nur Zeichen. Die Methode `_settled` war
  aus genau diesem Grund gestrichen worden.
- **`zip` bleibt ohne Aufrufer in `src/`.** Nur `zip_all` wird gebraucht. Bewusst behalten.
- **Der `ConstructionKey`-Block bleibt in jedem Modul dreiteilig.** Der Wächter fängt das Vergessen;
  eine Abstraktion darüber kostet mehr, als sie einspart.
