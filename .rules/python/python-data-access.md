# Python Data Access

> Uebersetzt `csharp-data-access.md` sinngemaess. Ueberschreibt das generische Repository-Pattern
> aus `common/patterns.md` — dieselbe Begruendung wie im C#-Original: eine generische Abstraktion
> verliert mehr (Query-Ausdruckskraft,
> Testbarkeit an der richtigen Stelle) als sie an Wiederverwendung gewinnt.
>
> Dieses Projekt hat aktuell **keinen festgelegten DB-/ORM-Stack** (leeres `pyproject.toml`,
> keine Dependencies). Die Regel bleibt deshalb bewusst **abstrakt** und nennt keine konkrete
> Bibliothek — sobald ein Stack (stdlib `sqlite3`, SQLAlchemy, …) feststeht, diese Datei um
> stack-spezifische Beispiele ergaenzen, analog zum C#-Original.

## Kein generisches Repository und kein Service-Locator-UnitOfWork

Kein generisches `Repository[TAggregate, TKey]`-`Protocol` und kein
`unit_of_work.get_repository(SomeType)`-Locator. Jedes Aggregat wird ueber einen **benannten,
schmalen Port** (`typing.Protocol`) mit domaenensprachlichen Methoden erreicht. Der
UnitOfWork-Port bleibt minimal — nur Commit.

Do:
```python
class SyncFileWriter(Protocol):
    def append(self, file: SyncFile) -> None: ...


class KnownPaths(Protocol):
    async def existing_among(self, candidates: Collection[RelativePath]) -> set[RelativePath]: ...


class UnitOfWork(Protocol):
    async def commit(self) -> None: ...  # kein rollback()
```

Don't:
```python
class Repository(Protocol[TAggregate, TKey]):
    async def get_by_id(self, id: TKey) -> TAggregate | None: ...
    def add(self, aggregate: TAggregate) -> None: ...
    def delete(self, id: TKey) -> None: ...  # Exception bei fehlendem Key = Kontrollfluss ueber Exception


class UnitOfWork(Protocol):
    def get_repository(self, repo_type: type[TRepo]) -> TRepo: ...  # Service Locator — versteckt Abhaengigkeiten
    async def rollback(self) -> None: ...                           # ueberfluessig, siehe unten
```

Ein generisches Repository ueber einer konkreten Datenbank-API wrappt meist etwas, das die API
selbst schon bereitstellt (eine Verbindung/Session *ist* bereits eine Unit of Work), und verliert
dabei Ausdruckskraft (rohe Query-Faehigkeiten, `JOIN`s, Projektionen). `rollback()` ist meist
unnoetig: `commit()` erst am Ende aufrufen — bei einem Fehler davor einfach nicht committen, die
Verbindung/Session wird verworfen, nichts wird persistiert. Unterschiedliche Aggregate haben
bewusst unterschiedliche Zugriffsformen; genau da schadet eine generische Abstraktion am meisten.
Ein benannter Read-Port mit domaenensprachlichen Methoden ist das richtige Modell, sobald ein
konkreter Query-Bedarf entsteht. Generisches CRUD nur bei einem echten Wechsel der
Persistenztechnologie oder bei vielen Aggregaten mit identisch trivialem CRUD in Erwaegung ziehen.

## Zeitpunkte als Unix-Sekunden-Value-Object

Zeitpunkte werden als **Unix-Sekunden (`int`)** gehalten und in ein eigenes Value Object
gewrappt — nicht als rohes `datetime`/`datetime` mit Zeitzone. Das haelt die Domaene
speichernah, deterministisch und frei von Zeitzonen-Mehrdeutigkeit; die Umrechnung passiert nur
am Rand, wenn ueberhaupt eine Anzeige noetig ist.

Do:
```python
@dataclass(frozen=True, slots=True)
class ExpiryTimestamp:
    unix_seconds: int
```

Don't:
```python
@dataclass(frozen=True, slots=True)
class ExpiryTimestamp:
    value: datetime  # Zeitzonen-/Serialisierungs-Mehrdeutigkeit am Persistenzrand
```

## Parameter-Limits bei grossen `IN`-Klauseln

Jede Datenbank-Engine begrenzt die Zahl gebundener Parameter je Statement (SQLite z. B. ueber
`SQLITE_MAX_VARIABLE_NUMBER`). Eine `IN`-Klausel, die pro Element einen eigenen gebundenen
Parameter erzeugt (`WHERE col IN (?, ?, ?, …)`), skaliert nicht auf grosse, potenziell
unbegrenzte Kandidatenmengen und wirft eine Fehlermeldung wie *"too many SQL variables"*.

Fuer einen serverseitigen, **unbegrenzten** `IN`-Vergleich: eine einzelne serialisierte
Kandidatenmenge (z. B. als JSON) als **einen** gebundenen Parameter uebergeben und
engine-seitig entpacken (SQLite: `json_each`; andere Engines haben ein Aequivalent), statt eines
Parameters je Element. Das gehoert hinter den Port (siehe oben) als reiner Read, nie als
LINQ-artiges `Contains`-Aequivalent direkt in Domaenencode.

Wird ein konkreter Stack gewaehlt, hier ein lauffaehiges Beispiel ergaenzen und einen Test
hinterlegen, der eine Kandidatenmenge oberhalb des Engine-Limits regressionssicher abdeckt.
