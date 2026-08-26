# Die Wurzel sammelt ihre Befunde selbst — das Validierungs-Behavior fällt weg

## Was entschieden wurde

`User.create` bricht nicht mehr beim ersten abgelehnten Feld ab. Es prüft alle fünf Felder und
meldet **alle** Befunde auf einmal, verpackt in einen Fall `UserRejected`.

Damit ist die Wurzel die einzige Stelle, an der eine Registrierung geprüft wird. Das
Validierungs-Behavior vor der Pipeline entfällt, und mit ihm das Regelwerk gegen das Request-DTO.

## Was daran der Punkt ist

[2026-08-26-2030](2026-08-26-2030-die-wurzel-haelt-ihre-invarianten-selbst.md) hielt fest, dass
**zweimal geparst** wird: einmal vom Regelwerk vor der Pipeline, um alle Feldfehler gesammelt als
422 zu melden, und einmal von `User.create`, weil eine Wurzel nur aus geprüften Werten entstehen
darf. Der Grund für die Doppelung war einzig, dass `create` fail-fast war und deshalb nur einen
Grund liefern konnte — der Vertrag in `contracts/pacts/identity/` verlangt aber drei Felder in einer
Antwort.

Der Grund ist weg, sobald die Wurzel sammelt. Die Doppelung ist damit auch weg, und mit ihr die
Möglichkeit, dass die beiden Wege auseinanderlaufen — was sie schon einmal getan hatten
([2026-08-21-2200](2026-08-21-2200-vertrag-zieht-anzeigename-und-zeitzone-nach.md)).

## Wie gesammelt wird: `zip_all` neben `zip`

`Result` bekommt neben `zip` einen zweiten Kombinator:

```python
def zip_all[U, E](self, other: Result[U, list[E]], /) -> Result[tuple[T, U], list[E]]
```

`zip` kürzt beim ersten Fehler ab, `zip_all` behält beide. Der Fehlerkanal ist eine **Liste**, und
sie steht schon im Eingang und nicht erst im Ausgang — nur so ist die Kette wieder ihr eigener
Eingang und `a.zip_all(b).zip_all(c)` bleibt flach. Jede `parse`-Factory hebt ihren Fehler per
`map_err` in eine einelementige Liste (`email_rejection` und die vier Geschwister in
[`user_creation_errors.py`](../../src/contexts/identity/domain/user_creation_errors.py)).

Das ist dieselbe Frage, die `all_of` in
[`validation.py`](../../src/contexts/shared_kernel/validation.py) beantwortet, nur für Ausgänge, die
neben dem Fehler auch einen **Wert** tragen: `all_of` sammelt Meldungen, `zip_all` sammelt Meldungen
und hält die geprüften Value Objects fest. Genau deshalb konnte die Wurzel die Aufgabe des Regelwerks
übernehmen, ohne ein zweites Mal zu parsen.

### Der annotierte `self` und die Varianz

`Err.zip_all` und `AsyncResult.zip_all` annotieren ihren `self` (`self: Err[list[X]]`), weil nur ein
Fehlschlag verkettet werden darf, der bereits eine Liste trägt. Ein annotierter `self` ist eine
Argument-Position; ein Klassen-Typparameter darin wäre invariant. Auf `AsyncResult` steht der
Erfolgs-Typ deshalb als eigener Parameter `V` und nicht als das kovariante `T` der Klasse — sonst
bricht `or_else`. Der Typprüfer hat das gemeldet, nicht ein Review.

## Was ersetzt wird

- **`validators/register_user_rules.py`** ist weg. Die fünf Regelfunktionen und
  `build_register_user_rules` waren die zweite Prüfung; sie hatten keinen Gegenstand mehr. Was
  bleibt, ist reine Übersetzung: die Fehler-Übersetzer je Feld und `to_field_errors`. Sie stehen
  jetzt als
  [`mappers/rejection_mapper.py`](../../src/contexts/identity/application/register_user/mappers/rejection_mapper.py)
  — ein Paket namens `validators/`, in dem keine Regel mehr steht, wäre eine falsche Behauptung.
- **`validating(...)` in der Pipeline** ist weg. Der Baustein selbst bleibt in
  `shared_kernel/behaviors/` bestehen — für Regeln, die eine Wurzel nicht beantworten kann.
- **`to_field_errors` ist nicht mehr unerreichbar.** Es ist jetzt der einzige Weg, auf dem ein 422
  entsteht. Der ganze Absatz „Diese Übersetzung ist im Regelbetrieb unerreichbar" aus
  [2026-08-26-2030](2026-08-26-2030-die-wurzel-haelt-ihre-invarianten-selbst.md) ist damit überholt.

## Was `.rules` nachziehen muss

[`python-rule-pattern.md`](../../.rules/python/python-rule-pattern.md) sagt an zwei Stellen, die
Collect-all-Regel werde gegen das public Request-DTO registriert und laufe als **erstes Behavior**
der Pipeline; die Command-Konstruktion sei deshalb infallibel. Für diesen Slice stimmt das nicht
mehr, und der Slice ist dort als Referenz benannt.

Nachgezogen sind die Verweise auf die verschobene Datei und der Abschnitt zum Behavior. Die Frage,
ob die Regel künftig generell „die Wurzel sammelt" heißt oder ob beide Formen nebeneinander gelten,
gehört in den Schritt, der `register_user` als Referenz-Slice festschreibt — nicht hierhin.

## Was offen bleibt

Unverändert aus [2026-08-26-2030](2026-08-26-2030-die-wurzel-haelt-ihre-invarianten-selbst.md):
`User` hat weiterhin **kein Verhalten außer `create`**. `UpdateProfile`, `ChangePassword` und
`RequestAccountDeletion` stehen aus.
