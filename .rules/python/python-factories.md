# Python Factories

> Uebersetzt `csharp-factories.md` sinngemaess. Python kennt keine
> echte Konstruktor-Sichtbarkeit (kein `private`) — die Regeln unten setzen den Schutz ueber
> Konvention (`_`-Praefix, `__all__`, `__post_init__`-Invarianten) statt ueber Sprachzwang um.

## Domaenen-benannte Factory-Funktionen statt generischer Konstruktion

Aggregate und Value Objects werden ueber **Modul-Level-Funktionen oder `classmethod`s mit
Domaenen-Verb** erzeugt — nie `new()`/`create()`/`build()`. Der rohe Konstruktor
(`__init__`/`Klasse(...)`) bleibt implementierungsseitig, wird aber nicht aus `__all__` exportiert
und nicht ausserhalb des Moduls direkt aufgerufen; die Factory ist der einzige vorgesehene Weg und
haelt die Domaeneninvarianten zentral.

Do:
```python
# sync_file.py
__all__ = ["SyncFile", "discover"]


@dataclass(frozen=True, slots=True)
class SyncFile:
    path: RelativePath
    state: SyncFileState


def discover(path: RelativePath, size: FileSize, last_write: LastWriteTime) -> SyncFile:
    return SyncFile(path, SyncFileState.Discovered(size, last_write))
```

Don't:
```python
# Aufrufer baut den rohen Konstruktor direkt zusammen, umgeht die Domaeneninvariante
file = SyncFile(path, SyncFileState.Discovered(size, last_write))  # ausserhalb des Moduls
```

## Separate Mapper-Funktionen fuer Nicht-Domaenen-Konstruktion

Konstruktionslogik, die nicht zum Domaenentyp selbst gehoert — Mapping aus Persistenz-Zeilen,
externen DTOs, Transportformaten — lebt in einer eigenen Modul-Funktion ausserhalb des Domaenen-
`dataclass`, nicht als Methode/`classmethod` darauf. Der Domaenentyp bleibt sauber; der Mapper
liegt im Infrastruktur-/Persistenz-Modul.

Do:
```python
# domain/order_line.py
@dataclass(frozen=True, slots=True)
class OrderLine:
    sku: str
    quantity: int
    price: float

# infra/order_line_mapper.py
def order_line_from_row(row: sqlite3.Row) -> OrderLine:
    return OrderLine(row["sku"], row["quantity"], row["price"])
```

Don't:
```python
@dataclass(frozen=True, slots=True)
class OrderLine:
    sku: str
    quantity: int
    price: float

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "OrderLine":  # Persistenz-Mapping im Domaenentyp
        return cls(row["sku"], row["quantity"], row["price"])
```

## Eine Factory-Funktion als einziger Einstiegspunkt

Fuer Service-/Handler-Konstruktion eine dedizierte Modul-Funktion nutzen, auch wenn sie nur ein
einzelnes Objekt zusammenbaut. Sie ist die eine Stelle, die bei Aenderung der Abhaengigkeiten
angepasst wird. Eine solche Funktion nicht als "duenner Wrapper ohne Wert" markieren — das
Zentralisieren der Konstruktion *ist* der Wert.

Do:
```python
def build_error_log_handler(container: Container) -> ErrorLogHandler:
    return ErrorLogHandler(
        writer=container.get(ErrorLogWriter),
        logger=container.get(Logger),
    )
```

Don't:
```python
# Konstruktion an jeder Aufrufstelle inline wiederholt
handler = ErrorLogHandler(writer, logger)  # dupliziert — bricht bei Signaturaenderung ueberall
```
