# Zwei Ergaenzungen ausserhalb des Referenz-Slice: `shared_kernel/validation.py` und `tzdata`

**Datum:** 2026-08-06, 11:05
**Anlass:** Bau von Ticket [0011](../issues/0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md),
Stufe 1 (`register_user`) — der Referenzimplementierung der Slice-Form dieses Repos.

Beide Aenderungen liegen ausserhalb des Slice und werden deshalb hier begruendet, statt
stillschweigend mitzulaufen.

## 1. Das Collect-all Rule Pattern landet im `shared_kernel`, nicht im Feature

**Entscheidung:** `Rule[T]`, `all_of` und `FieldError` leben in
`src/shared_kernel/validation.py`, nicht in `contexts/identity/application/register_user/`.

**Begruendung.** [`python-rule-pattern.md`](../../.rules/python/python-rule-pattern.md) verbietet
ausdruecklich, dass ein Feature den Rule-Typ strukturell nachbaut („Keine feature-lokale
`Protocol`-Klasse bildet `Rule`/`ResultRule` nach; Features importieren/komponieren den gemeinsamen
Typalias"). Einen gemeinsamen Typalias gab es bisher nicht — die Regel zeigte ins Leere. Haette
`register_user` sich einen eigenen gebaut, waere der zweite Slice gezwungen gewesen, entweder das
Duplikat anzulegen oder quer in einen fremden Use Case zu importieren. Beides ist schlechter als
die eine gemeinsame Definition.

**Warum das nicht der Frage vorgreift, was sonst in den `shared_kernel` wandert.** Diese Frage
bleibt offen und wird nach dem *zweiten* Slice entschieden (siehe
[`2026-08-06-0751`](2026-08-06-0751-slice-form-test-api-baureihenfolge.md), Antwort 6). Hier geht es
nicht um eine aus einem Feature extrahierte Abstraktion, sondern um die fehlende Haelfte eines
Musters, das bereits als Regel gilt und dessen andere Haelfte (`Result[T, E]`) schon im
`shared_kernel` liegt. Das Modul haengt ausschliesslich an der stdlib.

**Konsequenz.** Ein Slice, der Eingaben validiert, importiert `Rule`/`all_of`/`FieldError` von dort
und definiert nur seine eigenen Regel-Funktionen. Zu sehen in
`contexts/identity/application/register_user/validators/register_user_rules.py`.

## 2. `tzdata` wird Laufzeit-Dependency

**Entscheidung:** `tzdata>=2026.1` steht in `[project] dependencies`, nicht in den Dev-Extras.

**Begruendung.** `UserTimeZone` prueft eine IANA-Zeitzonen-Id gegen `zoneinfo.available_timezones()`.
Windows liefert keine IANA-Datenbank mit dem Betriebssystem aus; ohne `tzdata` ist die Menge dort
**leer**, und jede gueltige Eingabe — auch der Default `Europe/Berlin` — wird als unbekannte
Zeitzone abgelehnt. Das ist kein Testproblem: derselbe Code entscheidet in Produktion, in welcher
Zeitzone die Tagebuch-Tage eines Nutzers liegen (BACKEND.md, Abschnitt 0.4). Die Abhaengigkeit
gehoert deshalb zur Laufzeit, nicht zur Testumgebung.

**Konsequenz.** Der Aufruf ist ueber `functools.cache` gepuffert, weil `available_timezones()` bei
jedem Aufruf neu scannt und die Regel pro Request laeuft.

## Nicht entschieden

- Was **sonst** in den `shared_kernel` wandert — offen bis nach dem zweiten Slice.
- Ob `shared_kernel` in den `domain-purity`-Contract von `setup.cfg` aufgenommen wird. Solange
  `problem_details.py`, `idempotency.py` und `exception_handlers.py` aus den gemergten Tickets
  0005-0007 an pydantic/starlette haengen, wuerde der Contract sofort brechen. Der Kommentar in
  `setup.cfg` haelt das fest.
