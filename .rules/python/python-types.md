# Python Types

> Uebersetzt `csharp-types.md` sinngemaess. Ziel:
> **100 % annotierter Code**, durchgesetzt ueber ruffs `ANN`-Regelsatz; geprueft werden die
> Annotationen von **ty** (Issue #97), nicht von mypy/pyright.

## Variablendeklarationen

Jede public Funktions-/Methoden-Signatur ist vollstaendig annotiert (`ANN`-Pflicht). Fuer lokale
Variablen gilt das C#-Prinzip sinngemaess umgekehrt: annotiere nur, wenn der Typ aus der rechten
Seite **nicht** offensichtlich ist — eine redundante Annotation auf einem trivialen Literal fuegt
nichts hinzu.

Do:
```python
def build(customer_id: CustomerId, amount: float) -> Order:
    order = Order(customer_id, amount)  # Typ ergibt sich unmittelbar aus Order(...)
    result: Order | PendingOrder = _resolve(order)  # nicht aus dem Aufruf ersichtlich — annotiert
    return order
```

Don't:
```python
def build(customer_id, amount):  # fehlende ANN — von ruff geflaggt
    order: Order = Order(customer_id, amount)  # redundant, Typ ist evident
    return order
```

## `@final` als Standard fuer Klassen

Klassen sind standardmaessig mit `@typing.final` markiert. `@final` nur weglassen, wenn Vererbung
bewusst vorgesehen ist. `ty` setzt `@final` durch; unabhaengig davon bleibt es Pflicht als
dokumentierte Absicht fuer Leser:innen.

Do:
```python
@final
class OrderService:
    ...
```

Don't:
```python
class OrderService:  # offen fuer versehentliche Vererbung, keine Absicht dokumentiert
    ...
```

## `dataclass` fuer Datentypen

`@dataclass(frozen=True, slots=True)` fuer Datencontainer und Value Objects. Eine gewoehnliche
Klasse mit Methoden nur fuer Typen mit signifikantem Verhalten und internem, veraenderlichem
Zustand (siehe [python-code-organization.md](./python-code-organization.md)).

Do:
```python
@dataclass(frozen=True, slots=True)
class Customer:
    name: str
    email: str
```

Don't:
```python
class Customer:
    def __init__(self, name: str, email: str) -> None:
        self.name = name
        self.email = email
```

## Tagged Unions statt Enum fuer Zustand

Zustaende, geschlossene Wertemengen und kleine Algebren werden als **Tagged Union aus
`@dataclass(frozen=True)`-Varianten** modelliert — ein `|`-verknuepfter `type`-Alias (PEP 695, siehe
[python-modern-syntax.md](./python-modern-syntax.md)), dessen Varianten in genau einem Modul
definiert sind — nicht als `Enum` mit separatem `status`-Feld oder als nullable "Flag-Bag". Der
Zustand *ist* der Typ. Es gibt kein zusaetzliches `status: str`-Feld.

Do:
```python
@dataclass(frozen=True, slots=True)
class Copy:
    path: RelativePath


@dataclass(frozen=True, slots=True)
class Update:
    path: RelativePath
    size: FileSize


@dataclass(frozen=True, slots=True)
class Skip:
    reason: str


type SyncAction = Copy | Update | Skip
```

Don't:
```python
class SyncActionKind(Enum):
    COPY = auto()
    UPDATE = auto()
    SKIP = auto()


@dataclass(slots=True)
class SyncAction:
    kind: SyncActionKind          # Status-Feld statt Typ
    reason: str | None = None     # nullable Bag fuer variantenspezifische Daten
```

"Die Faelle tragen keine variantenspezifischen Daten" ist eine Falle: sobald gematcht wird,
tauchen fast immer Pro-Variante-Felder auf (ein Grund fuer einen Fehlschlag, Erwartet/Ist bei
einer Abweichung). Auf ein Primitiv abbilden nur an einer Protokoll-/Persistenzgrenze, ueber einen
`match` (siehe die Exhaustivitaetsregel in
[python-control-flow.md](./python-control-flow.md)) — intern bleibt es die Tagged Union.
