# Settings-Zugriff: Recherche zu `app.state` gegen Settings-Dependency

## Anlass

Nach der Welle, die `_register_user` von `Request` entkoppelt hat (Commit `5431b58`), blieb ein
Unbehagen: `request.app.state.settings` in [`src/api/composition.py`](../../src/api/composition.py)
greift durch die Anfrage hindurch auf die Anwendung zu, um an Konfiguration zu kommen. Die Frage
war, ob das ein Smell ist und was die belegte Alternative wäre.

Recherchiert wurde in drei getrennten Revieren: offizielle FastAPI-Doku, die Referenz-Repositories
des FastAPI-Autors, sowie Starlette-Doku und weitere Referenz-Implementierungen.

## Befunde, jeweils mit Quelle

### FastAPI rät von `app.state` ausdrücklich ab

Die API-Referenz schreibt zum `state`-Attribut der `FastAPI`-Klasse:

> „A state object for the application. This is the same object for the entire application, it
> doesn't change from request to request. **You normally wouldn't use this in FastAPI, for most of
> the cases you would instead use FastAPI dependencies.** This is simply inherited from Starlette."

Quelle: <https://fastapi.tiangolo.com/reference/fastapi/>

In den Tutorial-Seiten (Dependencies, Lifespan, Settings, Using the Request Directly) taucht
`app.state` überhaupt nicht auf. Das Lifespan-Beispiel unter
<https://fastapi.tiangolo.com/advanced/events/> benutzt statt `app.state` ein Modul-Dict
(`ml_models = {}`).

### Empfohlen ist die Settings-Dependency, begründet mit Testbarkeit

> „In some occasions it might be useful to provide the settings from a dependency, instead of
> having a global object with `settings` that is used everywhere. This could be especially useful
> during testing, as it's very easy to override a dependency with your own custom settings."

Muster: `get_settings()` als Funktion, injiziert per `Annotated[Settings, Depends(get_settings)]`.
Dazu `@lru_cache`, damit das Objekt nur einmal entsteht — die Doku begründet den Cache
**ausschließlich** mit Performance (Datei-I/O nicht je Anfrage wiederholen) und nennt keine
Nachteile.

Quelle: <https://fastapi.tiangolo.com/advanced/settings/>

### Der FastAPI-Autor injiziert Settings in seinem Produktions-Template gar nicht

Im `full-stack-fastapi-template`:

- `backend/app/core/config.py:88` → `settings = Settings()`, ein Modul-Singleton.
- Genutzt wird es überall per Import (`main.py`, `api/deps.py`, `core/db.py`), nie per `Depends()`.
- `app.state` kommt im Repo **nirgends** vor, auch nicht für Engine oder Session (Code-Suche: null
  Treffer).
- `app.dependency_overrides` produktiv: null Treffer.
- Die Engine ist ebenfalls Modul-Singleton (`core/db.py:6`); nur die pro-Anfrage-Session ist eine
  echte Dependency.

Quelle: <https://github.com/fastapi/full-stack-fastapi-template>

Die `get_settings()`+`@lru_cache`-Variante existiert nur in den Doku-Beispielen
(<https://github.com/fastapi/fastapi/tree/master/docs_src/settings>, `app02`/`app03`), und dort ist
ihre einzige Motivation, dass `test_main.py` sie per `dependency_overrides` austauschen kann.

### `dependency_overrides` ist nur testseitig dokumentiert

<https://fastapi.tiangolo.com/advanced/testing-dependencies/> rahmt den gesamten Abschnitt auf
Tests. Zur Produktivnutzung gibt es **keine Aussage** — weder befürwortend noch ablehnend. Ein
früher in der Sitzung geäußerter Einwand, produktives Überschreiben verbaue die Test-Naht, ist
damit unbelegt und wurde zurückgenommen.

### Der belegte Nachteil ist die Typisierung, nicht die Zugriffskette

- `State.__setattr__`/`__getattr__` sind auf `Any` typisiert; der Docstring nennt es „an object that
  can be used to store arbitrary state" (Starlette-Quellcode, `starlette/datastructures.py`).
- Starlette dokumentiert `app.state` nur als generische Ablage:
  <https://www.starlette.io/applications/>
- mypy erkennt dynamisch gesetzte State-Attribute nicht: <https://github.com/encode/starlette/issues/545>
- Externe Kritik mit derselben Stoßrichtung: adriangb, „Why there is no app.state in Xpresso",
  <https://dev.to/adriangb/why-there-is-no-appstate-in-xpresso-548i>

### `app.state` ist in der Praxis dennoch verbreitet

- `nsidnev/fastapi-realworld-example-app` holt seinen Datenbank-Pool in
  `app/api/dependencies/database.py` genau so aus `request.app.state.pool`.
- `Netflix/dispatch` hält Engine und `SessionLocal` modul-global und reicht nur den
  Anfrage-Handle über `request.state.db` (`src/dispatch/database/core.py`).

### Typisierter Lifespan-State existiert und funktioniert in diesem Stack

Seit Starlette 0.52.0 kann der Lifespan-Handler ein Dict per `yield {...}` herausgeben, das per
`TypedDict` typisiert und über `Request[State]` generisch abgerufen wird
(<https://www.starlette.io/lifespan/>).

Lokal gegen den installierten Stack geprüft (Starlette 1.3.1, FastAPI 0.141.1): das aus dem
Lifespan zurückgegebene Dict landet in `request.state`, und `Request[AppState]` ist subskribierbar
(`starlette.requests.Request[AppState]`); `fastapi.Request` **ist** `starlette.Request`. Zur
Laufzeit bleibt es ein `State`-Objekt — der Gewinn ist rein statisch.

## Was das für dieses Repository heißt

Zwei Randbedingungen dieses Repos entwerten die naheliegenden Alternativen:

1. **Die Startvalidierung.** `validate_settings()` läuft im Lifespan
   ([`src/main.py`](../../src/main.py)) und ist als die eine Quelle der Konfiguration gesetzt. Ein
   Modul-Singleton `settings = Settings()` — das Muster des Autors — verschiebt das Scheitern vom
   Start in den **Import**, also in jede Testsammlung und jedes Werkzeug, das die Anwendung gar
   nicht hochfährt. Genau dafür ist `src/settings.py` ein eigenes Modul.
2. **Es gibt keinen Typechecker.** Das Repo fährt ruff, und ruff ist Linter und Formatter, kein
   Typechecker: eine Datei mit `x: int = "keine Zahl"`, `y: str = laenge(42)` und
   `None.irgendwas()` passiert `ruff check` mit exit 0. Astrals Typechecker (`ty`) ist ein eigenes
   Werkzeug und nicht eingerichtet; [`pyproject.toml`](../../pyproject.toml) nennt mypy/pyright
   ausdrücklich als das, was hier nicht läuft. Der gesamte Nutzen eines typisierten States wäre
   damit heute von niemandem geprüft.

## Offen

Der Typechecker ist als [#97](https://github.com/mbalzert1978/fit_back/issues/97) aufgenommen —
solange er fehlt, ist ein typisierter State nicht sinnvoll entscheidbar.

Offen bleibt:

- Typechecker einrichten und danach über typisierten State entscheiden, oder
- auf das dokumentierte `get_settings()`-Muster wechseln — wobei dann zu klären ist, wie die
  Startvalidierung erhalten bleibt (ein Aufruf von `get_settings()` im Lifespan würde den Cache
  füllen und die Prüfung am Start halten).

Der Zustand nach Commit `5431b58` — `request_settings` im Composition Root als einzige Lesestelle —
bleibt bis dahin bestehen.
