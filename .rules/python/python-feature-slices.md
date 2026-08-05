# Python Feature-Slice-Form

> Uebersetzt `csharp-feature-slices.md` sinngemaess. Die
> C#-Vorlage referenziert ein konkretes fremdes Projekt (ADR-0009, `DhcpMacVerwaltung`,
> `MacSuche` als Vorlage-Feature) — hier stattdessen generisch. Sobald dieses Projekt ein erstes
> Referenz-Feature hat, diese Datei darauf verweisen lassen (analog zum C#-Original).

Gilt fuer jede Vertical-Slice-Operation: **`domain → application`**-Abhaengigkeitsrichtung strikt
einseitig, nie umgekehrt.

## Drei Schichten je Feature-Paket

Jedes Feature ist ein eigenes Python-Paket, intern geschichtet:

| Ordner | Inhalt | Erlaubte Abhaengigkeiten |
|--------|--------|--------------------------|
| `domain/` | Value Objects (`@dataclass(frozen=True, slots=True)`), Entitaeten, Aggregatwurzel, interne Ports (`Protocol`), interne Domaenen-Regeln (`ResultRule`, fail-fast, ein typisierter Fehler je Invariante) | **nur stdlib** — kein Drittanbieter-Paket, kein DI-Framework |
| `application/` | public Request-/Response-DTOs, public Ports (Gateway/Datenquelle) + deren Ergebnis-Typen, interner **Command** (VOs, ggf. unter `shared/` geteilt), interne **Handler** (Orchestrator), interne **Port-Adapter** (Domain-Port-Implementierung, Anti-Corruption-Layer), **Mapper** (je Richtung eine Funktion/Klasse), **Eingabe-Validierungsregeln** (`Rule Pattern`, collect-all, unter `validators/`), Wiring | `domain`, gemeinsames `common`-Paket, minimales DI (z. B. reine Funktionen/`functools.partial`, kein Framework noetig) |
| `tests/` | Tests ausschliesslich ueber eine public Test-API des Feature-Pakets | nur das Feature-Paket selbst (keine `_private`-Importe quer durchs Paket) |

`domain/` gliedert sich physisch in `entities/`, `value_objects/`, `ports/`, `rules/`; der
Namespace bleibt flach (Value-Object-Ergebnisse und Entitaeten referenzieren sich gegenseitig —
Unterpakete erzeugten zirkulaere Importe; die Domaene ist eine kohaerente Grenze). Innerhalb von
`application/` heisst kein Ordner `common` — das kollidiert mit einem echten geteilten
`common`-Paket; ein Ordner mit geteiltem Inhalt heisst `shared/`.

## Die Domaene spricht durchgehend `Result[T, E]` — ein flacher, feature-eigener Fehlertyp

Nicht nur Parse-Factories: **jeder** erwartete Fehlschlag innerhalb der Domaene — Ports, Domaenen-
Regeln, die Aggregatwurzel selbst — gibt `Result[T, E]` zurueck, mit **demselben einen, flachen**
feature-eigenen Fehlertyp (Tagged Union, ein Fall je Fehlerursache) als `E` durchgehend (siehe
[python-error-handling.md](./python-error-handling.md)). Der gemeinsame Fehlertyp macht eine
Uebersetzung an den Port-Grenzen ueberfluessig — Repository, Port und Aggregat reichen ihn
unveraendert durch.

## Die Domaene spricht nur VOs/Entitaeten — nie rohe Primitive

Primitive (`str`, `int`) leben **nur an den aeusseren Naehten**: den public Request-/Response-DTOs
und dem public Gateway. Der Adapter uebersetzt Primitiv↔VO. So wird Primitive Obsession an genau
einer Stelle geloest.

Do:
```python
def find_mac_in_scope(self, scope_id: ScopeId, target: Mac) -> "MacMatch": ...
```

Don't:
```python
def find_mac(self, scope_id: str, mac_input: str) -> object: ...  # Primitive Obsession in der Domaene
```

## Entitaet vs. Value Object — Identitaet ist ein validierter Typ

- **Value Object** = `@dataclass(frozen=True, slots=True)` (Wertgleichheit ueber alle Felder,
  von `@dataclass` automatisch generiert).
- **Entitaet** = Klasse mit **identitaetsbasierter** Gleichheit — eigenes `__eq__`/`__hash__` nur
  ueber das Identitaetsfeld, nicht ueber alle Attribute.
- Die **Identitaet ist ein validierter Typ, nie ein freier `str`**. Sie entsteht ueber eine
  Factory, die einen `Result` liefert statt zu werfen (erwarteter Fall, keine Exception).

Do:
```python
@dataclass(frozen=True, slots=True)
class ScopeId:
    value: str  # nur ueber parse(str) -> Result[ScopeId, str] erzeugt


class Scope:
    def __init__(self, id: ScopeId, leases: tuple[Lease, ...], reservations: tuple[Reservation, ...]) -> None:
        self.id = id
        self._leases = leases
        self._reservations = reservations

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Scope) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
```

Don't:
```python
class Scope:
    def __init__(self, scope_id: str) -> None:
        self.scope_id = scope_id  # "Foo" waere gleichermassen gueltig — keine Grenze, keine Identitaet
```

## Aggregatwurzel besitzt ihre Operationen (anti-anemic)

Die Wurzel haelt ihre Kinder und iteriert selbst; der Handler orchestriert nur. Das ist die
bewusste Ausnahme von [python-code-organization.md](./python-code-organization.md) ("Zustand von
Verhalten trennen") — jene Regel gilt fuer einfache Wertehalter/Projektionen, nicht fuer eine
Aggregatwurzel.

Do:
```python
class DhcpServer:
    def __init__(self, name: ServerName, scopes: tuple[Scope, ...]) -> None:
        self.name = name
        self._scopes = scopes

    def find_mac(self, target: Mac) -> "MacMatch":
        matches = [scope.find_mac(target) for scope in self._scopes]
        return MacMatch(
            leases=tuple(lease for m in matches for lease in m.leases),
            reservations=tuple(r for m in matches for r in m.reservations),
        )
```

Don't:
```python
matches = []
for scope in scopes:
    for lease in await gateway.get_leases(server, scope.id):
        if lease.mac == mac_input:
            matches.append(lease)  # Domaenenlogik im Handler
```

Ergebnisse einer Operation sind **geschlossene Tagged Unions**, nie `bool` + `Optional`-Ausgabe-
Tupel. Eine Operation, die zwei Fragen in einem Flag beantwortet, ist zwei Operationen — trenne sie
in zwei Slices, nicht ein Flag im Handler.

## Repository materialisiert die Aggregatwurzel per Identitaet

Der Domain-Port (`ports/`) laedt die Wurzel; die Application-Bridge implementiert ihn ueber die
Gateway-Naht und uebersetzt Rohdaten in Entitaeten/VOs. Der Port ist wie jeder andere
Domaenenbaustein ehrlich fehlbar (`Result[T, E]`) — der Bridge-Adapter faengt dabei nichts selbst
(siehe unten); muss der Port mehrere, voneinander unabhaengige Teilladungen zusammenfuehren, tut
er das per `asyncio.TaskGroup`.

```python
class DhcpServerRepository(Protocol):
    async def load(self, server: ServerName) -> "Result[DhcpServer, DomainError]": ...


class DhcpServerRepositoryAdapter:
    def __init__(self, gateway: MacSearchDhcpGateway) -> None:
        self._gateway = gateway

    async def load(self, server: ServerName) -> "Result[DhcpServer, DomainError]":
        match await self._gateway.get_scopes(server.value):
            case ScopesFound(scopes=scopes):
                async with asyncio.TaskGroup() as tg:
                    tasks = [tg.create_task(self._load_scope(server, s.scope_id)) for s in scopes]
                return Ok(DhcpServer(server, tuple(t.result() for t in tasks)))
            case ServerUnknown():
                return Err(ServerUnknownError(server))
```

## Handler, Adapter, Mapper sind verschiedene Dinge

Die Rollen werden **nie** in einer Klasse/Funktion vermischt.

| Rolle | Was sie ist | Was sie NICHT tut |
|-------|-------------|-------------------|
| **Handler** (`Protocol`, ~10-15 Zeilen Implementierung) | **Orchestrator**: Aggregat ueber das Repository laden → **eine** Domaenen-Operation rufen → deren Ergebnis als internen **Outcome** zurueckgeben | Kennt weder Request- noch Response-DTO, kein Parsen, kein Mapping, kein IO, kein `try`/`except`, keine Fachlogik |
| **Port-Adapter** (`…Repository`, `…MutationAdapter`) | ACL nach unten: implementiert einen Domain-Port ueber ein public Gateway; uebersetzt Primitiv↔VO in beide Richtungen; wird per DI injiziert | Keine Orchestrierung |
| **Request-Mapper** (`<op>_request_mapper.py`) | Uebersetzt Request-DTO → Command, 1:1, ohne Seiteneffekt. Hier lebt das sichere Re-Parsen (`hydrate`, `AssertionError`) | Keine Fachentscheidung, kein IO, kein Rueckweg |
| **Response-Mapper** (`<op>_response_mapper.py`) | Uebersetzt Outcome → Response-Tagged-Union, 1:1, ohne Seiteneffekt; formuliert die Anzeigemeldung je Fehlerfall | Keine Fachentscheidung, kein IO, kein Hinweg |

Damit kreuzt **kein DTO** die Grenze zum Handler und **kein Domaenentyp** die public Naht:

```
Request (public DTO) ─► RequestMapper ─► Command (intern, VOs) ─► Handler ─► Domaene
Response (public DTO) ◄─ ResponseMapper ◄─ Outcome (intern, Tagged Union) ◄─ Handler ◄─ Domaene
```

**Command** ist ein `@dataclass(frozen=True, slots=True)` aus fertig geparsten VOs. Teilen sich
zwei Operationen dasselbe Eingabetupel, teilen sie sich auch den Command — zwei identische
Dataclasses nebeneinander sind keine Trennung, nur Duplikat.

**Outcome** braucht es nur, wenn die Operation einen Fehlschlag kennt, der *dem Slice* gehoert und
nicht der Domaene. Ist das Domaenen-`Result` bereits das vollstaendige Ergebnis, gibt der Handler
es **direkt** zurueck (`Handler = Callable[[Command], Result[Order, DomainError]]`) — ein Wrapper,
der nur einen Fall umhuellt, ist Zeremonie.

### Ein Mapper pro Richtung, nicht einer pro Operation

**Hinein und heraus sind zwei Funktionen/Klassen.** Sie teilen weder Zustand noch Hilfsmittel; sie
stehen nur zufaellig am selben Naht-Punkt. Der Response-Mapper waechst mit jedem neuen Fehlerfall,
der Request-Mapper bleibt eine Zeile. Kein Mapper bedient mehrere Operationen — auch dann nicht,
wenn zwei Operationen heute dieselbe Response-Form haben; die Antwort gehoert der Operation, und
identische Form heisst nicht identische Bedeutung.

## Keine Exception als Kontrollfluss — auch nicht im Adapter

Gilt unveraendert auch innerhalb eines Feature-Slices: Handler und Port-Adapter fangen nie, nur die
IO-/Infrastruktur-Implementierung hinter der Naht (siehe
[python-error-handling.md](./python-error-handling.md), "Nur an der IO-Naht fangen").

## Illegal States Unrepresentable & deklarativer Stil

Ergebnisse als geschlossene Tagged Union statt `bool` + `Optional`, nullable + Nachricht oder
Exception fuer einen erwarteten Fall — Tagged Unions ersetzen `Enum` **und** `None`
([python-types.md](./python-types.md), [python-error-handling.md](./python-error-handling.md)).
Deklarativer, zeitgemaesser Stil gilt unveraendert auch in Handlern
([python-modern-syntax.md](./python-modern-syntax.md),
[python-control-flow.md](./python-control-flow.md)).

## Review-Checkliste

- [ ] `domain/` haengt nur an der stdlib; `application/` bruecke zu geteiltem `common`/minimalem Wiring; `tests/` nur an das Feature-Paket.
- [ ] Domaene spricht nur VOs/Entitaeten; Primitive ausschliesslich in Request-/Response-DTOs + Gateway.
- [ ] Entitaeten haben identitaetsbasierte Gleichheit; VOs sind `@dataclass(frozen=True, slots=True)`; Identitaet ist ein validierter Typ, kein freier `str`.
- [ ] Aggregatwurzel besitzt Operationen und Iteration; der Handler orchestriert nur (~10-15 Zeilen).
- [ ] Domain-Ports, Domain-Regeln und Aggregatwurzel geben durchgehend `Result[T, E]` mit **demselben einen, flachen** feature-eigenen Fehlertyp zurueck.
- [ ] Repository materialisiert die Wurzel per Identitaet (ehrlich fehlbar); externe Abhaengigkeiten nur hinter der public Naht; Rekonstruktion aus vertrauenswuerdiger Quelle nutzt `hydrate`, nicht `parse`.
- [ ] **Handler orchestriert nur**, baut keine Ports selbst, bekommt sie per DI/Parameter.
- [ ] **Kern-Handler kennt weder Request- noch Response-DTO** — Parsen und Mapping stehen in den Mappern.
- [ ] **Mapper je Richtung eine eigene Funktion/Klasse** — keine Funktion mit beiden Richtungen, kein Mapper fuer mehrere Operationen.
- [ ] **Outcome ist nur ein eigener interner Typ, wenn die Operation einen slice-eigenen Fehlschlag kennt**; sonst gibt der Handler das Domaenen-`Result` direkt zurueck.
- [ ] **Kein try/except in Handler/Adapter**; erwartete Fehlschlaege sind Ergebnis-Typen im Naht-Vertrag, das Fangen lebt in IO/Infrastruktur.
- [ ] Ergebnisse als geschlossene Tagged Union; kein `bool`/`None`/`Enum` fuer Zustand.
