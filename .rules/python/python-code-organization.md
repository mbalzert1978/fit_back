# Python Code Organization

> Uebersetzt `csharp-code-organization.md` sinngemaess.

## Aussagekraeftige Namen

Namen muessen die Absicht ohne umliegenden Kontext erkennen lassen. Keine Abkuerzungen, keine
generischen Namen, keine Typ-Suffixe im Namen selbst. Vollstaendige Typannotation (durch ruffs
`ANN`-Regeln erzwungen) ersetzt den in C# noetigen Typnamen im Bezeichner.

Do:
```python
async def process_order(request: OrderRequest, *, timeout: float) -> Result[Order, OrderError]: ...
```

Don't:
```python
async def proc(r: dict, t: float) -> object: ...
```

## Zustand von Verhalten trennen

Typen halten entweder Daten (`@dataclass`) oder implementieren Verhalten (Funktionen/Klassen mit
Methoden), nicht beides zugleich als aufgeblaehte Klasse mit Mutation.

**Gilt fuer einfache, nicht-identitaetstragende Wertehalter** (Read-Models, Projektionen, DTO-nahe
Datentypen) — **nicht** fuer eine Aggregatwurzel. Eine Aggregatwurzel besitzt ihre Operationen als
Methoden und iteriert selbst ueber ihre Kinder; das ist die bewusste Ausnahme von "Zustand ist
niemals mit Verhalten vermischt" und in [python-feature-slices.md](./python-feature-slices.md)
("Aggregatwurzel besitzt ihre Operationen") beschrieben. Das Beispiel unten (`OrderSummary`) ist
absichtlich **kein** Aggregat, sondern eine reine Projektion — bei einer echten Aggregatwurzel wie
`Order` innerhalb eines Feature-Slices gilt stattdessen die Regel aus feature-slices.md.

Do:
```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OrderLine:
    price: float
    quantity: int


@dataclass(frozen=True, slots=True)
class OrderSummary:
    id: OrderId
    lines: tuple[OrderLine, ...]


def calculate_total(summary: OrderSummary) -> float:
    return sum(line.price * line.quantity for line in summary.lines)
```

Don't:
```python
class OrderSummary:
    def __init__(self, lines: list[OrderLine]) -> None:
        self.lines = lines
        self.total: float = 0.0

    def calculate_and_update_total(self) -> None:
        self.total = sum(line.price * line.quantity for line in self.lines)
```

## Reine Funktionen bevorzugen

Funktionen ohne Seiteneffekte sind isoliert testbar und leichter nachvollziehbar.

Do:
```python
def calculate_total_price(lines: Iterable[OrderLine], tax_rate: float) -> float:
    return sum(line.price * line.quantity for line in lines) * (1 + tax_rate)
```

Don't:
```python
def calculate_and_update_total_price(self) -> None:
    self.total = sum(line.price * line.quantity for line in self.lines)
    self._update_database()  # Seiteneffekt in der Berechnung vermischt
```
