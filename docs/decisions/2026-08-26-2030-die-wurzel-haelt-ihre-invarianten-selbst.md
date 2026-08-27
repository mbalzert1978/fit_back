# Die Wurzel hält ihre Invarianten selbst

**Entschieden am 2026-08-26, 20:30.**

## Was entschieden wurde

Zwei Dinge, die zusammengehören.

**1. Kein Value Object entsteht mehr über seinen rohen Konstruktor.**

Jedes Value Object des Identity-Context hält ein modul-privates `ConstructionKey`
([`shared_kernel/construction.py`](../../src/contexts/shared_kernel/construction.py)) und weist im
`__post_init__` jeden Bau ab, der es nicht vorzeigen kann. Offen bleiben nur `parse`, `hydrate` und
— bei `UserId` — `generate`. Dasselbe gilt für die Aggregatwurzel `User`; ihr einziger Weg herein
ist `User.create`.

**2. `User.create` nimmt Rohwerte, baut die Value Objects selbst und darf ablehnen.**

Das frühere modul-freie `register(...)` ist weg. An seiner Stelle steht eine `classmethod` auf der
Wurzel, die `str` entgegennimmt, jedes Feld selbst parst und `Result[User, UserCreationError]`
liefert. Identität, Passwort-Hash und Zeitpunkt entstehen **in** `create`; die drei dafür nötigen
Ports (`IdnEncoder`, `PasswordHasher`, `TimeProvider`) kommen per Dependency Injection herein.

Damit trägt `RegisterUserCommand` nur noch Primitive, und der Request-Mapper parst nicht mehr —
er bildet nur noch die Feldnamen des Vertrags auf die internen ab.

## Warum

Das Domänenmodell war anämisch. `User` hatte vier Dunder und sonst nichts, und `register(...)` war
infallibel, weil alle Entscheidungen schon eine Schicht weiter außen gefallen waren: der
Request-Mapper baute die Value Objects, die Wurzel nahm sie entgegen. Wer entschied, welche Regeln
ein `Email` gesehen hat, war damit der Aufrufer — nicht die Domäne.

Dazu kam ein Loch, das seit dem ersten Slice offen stand: `Email("quatsch")` ging durch. Die
Docstrings sagten „wird ausschließlich über `parse` oder `hydrate` erzeugt", aber das war Prosa,
keine Sperre. Jede Zusicherung darüber, was ein Value Object enthält, hing daran, dass niemand den
Konstruktor benutzt.

Beides zusammen heißt jetzt: **es gibt genau einen Weg zu einem `User`, und der prüft alles.**

## Was dadurch ausgeschlossen ist

- **`__post_init__`, das die Regeln nachprüft.** Wäre die naheliegende Sperre, scheitert aber an
  `Email`: `domain_is_valid` braucht den `IdnEncoder`, und ein `__post_init__` bekommt ihn nicht.
  Der Schlüssel prüft deshalb den **Weg** statt des Werts — und der eine Weg, der bleibt, prüft den
  Wert vollständig.
- **Ein geteilter Schlüssel im Shared Kernel.** Wäre er exportiert, könnte ihn jedes Modul
  importieren, und die Sperre wäre nur noch eine Bitte. Jedes Value-Object-Modul hält seinen
  eigenen; geteilt ist nur die Form (`ConstructionKey`, `deny_foreign_key`).
- **Eine flache Fehler-Union aus den Parser-Fehlern.** `EmailIsEmpty | PasswordTooShort | …` verlöre,
  zu **welchem Feld** ein Fall gehört. Stattdessen fünf Hüllen in
  [`user_creation_errors.py`](../../src/contexts/identity/domain/user_creation_errors.py), eine je
  Feld.
- **Ports als Attribute der Wurzel.** `User` hält weder Uhr noch Hasher. Sie werden an `create`
  übergeben und sind nach dem Aufruf wieder weg.

## Was daran nicht selbsttragend ist

**Es wird zweimal geparst.** Das Regelwerk vor der Pipeline parst, um alle Feldfehler auf einmal zu
melden (422 laut `contracts/pacts/identity/`), und `User.create` parst noch einmal, weil eine Wurzel
nur aus geprüften Werten entstehen darf. Der Fehlerkanal von `create` ist im Regelbetrieb deshalb
unerreichbar.

Er wird trotzdem übersetzt und nicht wegbehauptet: `to_field_errors` in
[`validators/register_user_rules.py`](../../src/contexts/identity/application/register_user/validators/register_user_rules.py)
bildet ihn auf dieselben Feldfehler ab, die auch das Regelwerk liefert. Die beiden Wege waren schon
einmal auseinandergelaufen (`DisplayName`, Vertrag gegen Invariante, siehe
[2026-08-21-2200](2026-08-21-2200-vertrag-zieht-anzeigename-und-zeitzone-nach.md)); ein
`AssertionError` an dieser Stelle machte aus einer stillen Abweichung einen 500er statt eines
ehrlichen 422.

`tests/contexts/identity/test_user_creation.py` fährt die fünf Ablehnungen direkt an der Wurzel an,
`tests/contexts/identity/test_value_object_construction.py` die Sperre.

## Was offen bleibt

`User` hat weiterhin **kein Verhalten außer `create`**. `UpdateProfile`, `ChangePassword` und
`RequestAccountDeletion` stehen in [`BACKEND.md`](../Draft/BACKEND.md) Abschnitt 1, und die
Invariante „ein `PendingDeletion`-Konto kann sich nicht mehr anmelden" hält heute niemand. Das ist
der verbleibende Rest der Anämie, und er gehört in die Tickets dieser Use Cases — nicht hierhin.
