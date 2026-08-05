# Python Dependency Management

> Uebersetzt `csharp-dependencies.md` sinngemaess.

## Konstruktor-Injection minimal halten

Halte `__init__`/den Dataclass-Konstruktor schlank. Viele Parameter signalisieren zu viele
Verantwortlichkeiten. Einmal-genutzte Abhaengigkeiten als Funktionsparameter uebergeben statt sie
im Zustand zu halten.

Do:
```python
@dataclass(slots=True)
class OrderService:
    repository: OrderRepository

    async def process(self, order: Order, notifier: NotificationService) -> None:
        ...
```

Don't:
```python
@dataclass(slots=True)
class OrderService:
    repository: OrderRepository
    notifier: NotificationService
    payment: PaymentProcessor
    inventory: InventoryService
    metrics: MetricsService  # zu viele — Verantwortlichkeiten aufsplitten
```

## Komposition ueber `Protocol` statt Vererbung

Komplexes Verhalten durch Zusammensetzen fokussierter `Protocol`-Typen bauen, nicht durch
Vererbung von Basisklassen. Pythons strukturelles Typsystem (`typing.Protocol`) macht das ohne
gemeinsame Basisklasse moeglich — Duck Typing ist hier das eingebaute Aequivalent zu Interfaces.

Do:
```python
class Logger(Protocol):
    def log(self, message: str) -> None: ...


@dataclass(slots=True)
class EnhancedLogger:
    base_logger: Logger
    metrics: Metrics

    def log(self, message: str) -> None:
        self.base_logger.log(message)
        self.metrics.increment("log_count")
```

## Logging ist ein Decorator, keine Konstruktor-Abhaengigkeit

Fachliche Typen — Handler, Domain-Services, Prozessoren — nehmen keinen Logger entgegen. Das
Logging-Anliegen gehoert in einen dedizierten Decorator, der den Port umschliesst, damit der
Kerntyp eine einzige Verantwortung behaelt.

Do:
```python
class FetchHandler(Protocol):
    async def handle(self, request: FetchRequest) -> FetchOutcome: ...


@dataclass(slots=True)
class PlainFetchHandler:
    source: FetchSource

    async def handle(self, request: FetchRequest) -> FetchOutcome:
        return await self.source.fetch(request)  # kein Logger — reine Orchestrierung


@dataclass(slots=True)
class LoggingFetchHandler:
    inner: FetchHandler
    logger: Logger

    async def handle(self, request: FetchRequest) -> FetchOutcome:
        self.logger.info("fetching %s", request.path)
        return await self.inner.handle(request)
```

Don't:
```python
@dataclass(slots=True)
class FetchHandler:
    source: FetchSource
    logger: Logger  # Logging-Anliegen in den fachlichen Typ geleakt
```

## Public Protocol statt Zugriff auf `_private`-Module ueber Paketgrenzen

Braucht ein anderes Paket einen Typ, der `_intern` in einem anderen Modul liegt, wird ein
**public `Protocol`** exportiert und per Dependency Injection (Konstruktor-/Funktionsparameter)
uebergeben. Nicht ein `_`-praefigiertes Modul/Objekt direkt paketuebergreifend importieren — das
ist das Python-Aequivalent zu C#s `[InternalsVisibleTo]`-Missbrauch.

Do:
```python
# im besitzenden Paket, public_api.py
class OutboxRunner(Protocol):
    async def run(self) -> None: ...

# _internal.py — Implementierungsdetail
class _OutboxProcessor:
    async def run(self) -> None: ...

# Wiring, z. B. main.py:
runner: OutboxRunner = _OutboxProcessor()
```

Don't:
```python
# in einem anderen Paket
from other_package._internal import _OutboxProcessor  # importiert bewusst privates Implementierungsdetail
```

Der `_`-Praefix bleibt ausschliesslich fuer Test-Module reserviert, die absichtlich auf interne
Details zugreifen wollen (Python hat keine harte Zugriffskontrolle — die Konvention *ist* die
Grenze, also wird sie nicht durch andere Produktionspakete unterlaufen).
