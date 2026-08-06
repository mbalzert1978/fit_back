# Python Feature-Slice-Form

> Uebersetzt `csharp-feature-slices.md` sinngemaess. Die
> C#-Vorlage referenziert ein konkretes fremdes Projekt (ADR-0009, `DhcpMacVerwaltung`,
> `MacSuche` als Vorlage-Feature).
>
> **Referenzimplementierung dieses Repos: `src/contexts/identity`, Use Case `register_user`**
> (Ticket 0011, Stufe 1). Jede Regel unten ist dort gebaut zu sehen — im Zweifel gilt der Code
> als Vorbild, nicht die Prosa. Wer einen neuen Slice anlegt, liest zuerst
> `src/contexts/identity/application/register_user/` und danach diese Datei.

Gilt fuer jede Vertical-Slice-Operation: **`domain → application`**-Abhaengigkeitsrichtung strikt
einseitig, nie umgekehrt.

## Drei Schichten je Feature-Paket

Jedes Feature ist ein eigenes Python-Paket, intern geschichtet:

| Ordner | Inhalt | Erlaubte Abhaengigkeiten |
|--------|--------|--------------------------|
| `domain/` | Value Objects (`@dataclass(frozen=True, slots=True)`), Entitaeten, Aggregatwurzel, interne Ports (`Protocol`), interne Domaenen-Regeln (`ResultRule`, fail-fast, ein typisierter Fehler je Invariante) | **nur stdlib** — kein Drittanbieter-Paket, kein DI-Framework |
| `application/` | public Request-/Response-DTOs, public Ports (Gateway/Datenquelle) + deren Ergebnis-Typen, interner **Command** (VOs, ggf. unter `shared/` geteilt), interne **Handler** (Orchestrator), interne **Port-Adapter** (Domain-Port-Implementierung, Anti-Corruption-Layer), **Mapper** (je Richtung eine Funktion/Klasse), **Eingabe-Validierungsregeln** (`Rule Pattern`, collect-all, unter `validators/`), **Test-API + In-Memory-Fakes** (siehe unten — Teil des Slice, nicht des Testprojekts), Wiring | `domain`, gemeinsames `common`-Paket, minimales DI (z. B. reine Funktionen/`functools.partial`, kein Framework noetig) |
| `tests/` | Tests ausschliesslich ueber die public Test-API des Use Case | nur das Feature-Paket selbst (keine `_private`-Importe quer durchs Paket) |

Ein **Bounded Context** ist die Feature-Paket-Grenze: **eine** `domain/`-Schicht, darunter **je Use Case
ein eigener `application/<use_case>/`-Ordner**. Der Fehlertyp (`Result[T, E]`, siehe unten) ist damit
**context-eigen**, nicht use-case-eigen — alle Use Cases eines Contexts teilen ihn.

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

## Die Naht gehoert dem Use Case — kein geteiltes Gateway

Die **Domaene gibt die Ports vor, die sie braucht** (`domain/ports/`, `Protocol`). Der Use Case
**adaptiert** sie und formuliert daraus seine **eigene, schmale public Anforderung** nach aussen —
die Naht. Zwei Use Cases, die zufaellig dieselbe Datenquelle brauchen, bekommen **zwei eigene
Nahtvertraege**, nie einen geteilten „Universal-Gateway". Ein geteiltes Gateway koppelt Use Cases
aneinander, die einander nichts angehen, und waechst zwangslaeufig zur Sammelschnittstelle.

Drei Regeln fuer jede Naht:

1. **Nur die Operationen, die dieser Use Case wirklich braucht** — nicht die, die die Datenquelle
   anbietet.
2. **Ueber die Naht wandern ausschliesslich Primitive** (`str`, `int`, einfache Records daraus). Kein
   VO, keine Entitaet, kein Aggregat. Die Uebersetzung Primitiv↔VO ist Aufgabe des Port-Adapters.
3. **Die Naht liefert ihre eigene, einfache Tagged Union**, nicht `Result[T, E]` — `Result` ist der
   Domaenen-Fehlerkanal und bleibt domaenenseitig. Die public Naht kennt ihn nicht.

Do:
```python
class RegisterUserIdentityGateway(Protocol):
    """Public Naht des Use Case — nur Primitive, eigenes Ergebnis-Union."""

    async def find_by_email(self, email: str) -> "EmailLookup": ...


type EmailLookup = EmailTaken | EmailFree          # eigene Union, KEIN Result[T, E]


@dataclass(frozen=True, slots=True)
class EmailTaken:
    user_id: str                                    # Primitiv, kein UserId-VO


@dataclass(frozen=True, slots=True)
class EmailFree:
    pass
```

Don't:
```python
class IdentityGateway(Protocol):                    # geteiltes Sammel-Gateway ueber alle Use Cases
    async def find_by_email(self, email: Email) -> Result[User, DomainError]: ...
    #                              ^ VO ueber der Naht      ^ Result auf der public Seite
    async def save(self, user: User) -> None: ...   # Operation, die dieser Use Case nicht braucht
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

## Die Test-API ist Teil des Slice, nicht des Testprojekts

**Je Use Case eine Test-API**, ausgeliefert unter `application/<use_case>/test_api.py`, die
In-Memory-Fakes daneben unter `application/<use_case>/fakes/`. Sie ist **kein** Testcode und
**kein** Mock-Gerüst, sondern die oeffentliche Bedien-Oberflaeche des Slice fuer alles, was ihn
verhaltensseitig pruefen will.

Sie verdrahtet **dieselbe Pipeline wie die Produktion** — Request-Mapper → Handler →
Response-Mapper, inklusive Validierungsregeln — und tauscht **ausschliesslich an der aeussersten
Naht** den In-Memory-Fake ein. Nichts dazwischen wird gemockt.

| Phase | Laeuft ueber |
|-------|--------------|
| **Arrange** | fluente Methoden der Test-API (`with_…`), die den Fake befuellen — der Test kennt die Fake-Klasse nie |
| **Act** | das **echte** public Request-DTO des Use Case, durch die **echte** Pipeline |
| **Assert** | die **echte** Response-Tagged-Union des Use Case |

Damit ist ein Slice **vollstaendig verhaltensgetestet, bevor eine Zeile Infrastruktur existiert** —
keine Datenbank, kein HTTP, kein FastAPI, kein Container.

```python
@final
class RegisterUserTestApi:
    """Public Test-API des register_user-Slice."""

    def __init__(self) -> None:
        self._gateway = InMemoryRegisterUserIdentityGateway()

    # --- Arrange ---
    def with_existing_user(self, email: str, user_id: str = "…") -> "RegisterUserTestApi":
        self._gateway.add_user(email, user_id)
        return self

    # --- Act: echtes Request-DTO durch die echte Pipeline ---
    async def run(self, request: RegisterUserRequest) -> RegisterUserResponse:
        return await build_register_user_pipeline(self._gateway).run(request)
```

```python
async def test_lehnt_bereits_vergebene_email_ab() -> None:
    api = RegisterUserTestApi().with_existing_user("a@b.de")

    result = await api.run(RegisterUserRequest(email="a@b.de", password="…"))

    assert isinstance(result, RegisterUserResponse.EmailBereitsVergeben)
```

Was die Test-API **nicht** ist: sie testet den Slice gegen In-Memory-Fakes. **Integrations- und
End-to-End-Tests gegen echte Infrastruktur** (Testcontainers/Postgres, HTTP gegen die laufende App)
sind eine **eigene, aeusserste Testebene** und ausdruecklich **nicht** Teil der Test-API — siehe
[`docs/milestones/02-test-pyramide.md`](../../docs/milestones/02-test-pyramide.md).

## Baureihenfolge: Domaene zuerst, Infrastruktur zuletzt

Ein Slice wird **von innen nach aussen** gebaut, und er ist **fertig und abnehmbar, bevor
Infrastruktur existiert**:

1. **`domain/`** — VOs, Entitaeten, Aggregatwurzel, Ports, Regeln. Nur stdlib.
2. **`application/<use_case>/`** — Command, Handler, beide Mapper, Validierungsregeln, Port-Adapter,
   die public Naht (Protocol + Ergebnis-Union).
3. **Test-API + In-Memory-Fake + Specs** — ab hier ist das Verhalten des Slice **vollstaendig**
   spezifiziert und gruen.
4. **`infrastructure/`** — erst jetzt: die echte Naht-Implementierung (SQLAlchemy-Repository,
   externer Adapter).
5. **`src/api/<context>/`** — zuletzt der HTTP-Router: nur HTTP ↔ Application-DTO.

Wer Schritt 4 oder 5 vor Schritt 3 baut, hat den Slice nicht geschnitten, sondern eine Schicht.
**Ein Ticket, das nur Schritt 4 oder 5 liefert, ist kein Tracer Bullet** — siehe die
Ticket-Schnitt-Regel in [`docs/milestones/00-overview.md`](../../docs/milestones/00-overview.md).

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
- [ ] **Ein Bounded Context = eine `domain/`-Schicht + je Use Case ein `application/<use_case>/`**; der `Result`-Fehlertyp ist context-eigen, nicht use-case-eigen.
- [ ] **Die Naht gehoert dem Use Case**: eigener, schmaler Vertrag statt geteiltem Gateway; nur die Operationen, die dieser Use Case braucht.
- [ ] **Ueber die public Naht wandern nur Primitive** — kein VO, keine Entitaet, kein Aggregat.
- [ ] **Die public Naht liefert eine eigene, einfache Tagged Union**, nie `Result[T, E]` — der bleibt domaenenseitig.
- [ ] **Test-API je Use Case** unter `application/<use_case>/test_api.py`, In-Memory-Fakes unter `application/<use_case>/fakes/` — Teil des ausgelieferten Slice, nicht des Testprojekts.
- [ ] **Test-API verdrahtet die echte Pipeline** (Request-Mapper → Handler → Response-Mapper + Validierung) und tauscht nur an der aeussersten Naht den Fake ein; nichts dazwischen wird gemockt.
- [ ] **Specs: Arrange ueber die Test-API, Act ueber das echte Request-DTO, Assert gegen die echte Response-Union** — kein Test greift auf Handler, Domaene oder Fake direkt zu.
- [ ] **Der Slice ist ohne Infrastruktur vollstaendig gruen** (keine DB, kein HTTP, kein Container); Integrations-/E2E-Tests sind eine eigene, aeusserste Ebene.
- [ ] **Baureihenfolge eingehalten**: `domain/` → `application/<use_case>/` → Test-API + Specs → `infrastructure/` → `src/api/`.
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
