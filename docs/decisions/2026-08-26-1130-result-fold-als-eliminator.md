# `Result` bekommt einen Eliminator: `fold`

**Datum:** 2026-08-26, 11:30
**Status:** entschieden, umgesetzt (Issue [#100](https://github.com/mbalzert1978/fit_back/issues/100))

## Der Anlass

Der Abbau der `ty`-Baseline (#97, Welle 2) hat an sieben Stellen dieselbe Verrenkung erzwungen:
einen **zweistufigen `match`**, erst ueber den Ausgang (`Ok`/`Err`), dann ueber den Fehlerwert.
Zwei `assert_never` je Funktion, eine Einrueckungsebene mehr, und die Fachlogik eine Ebene tiefer,
als sie es verdient.

Gemessen an einer Minimal-Probe traegt `ty` die Einengung aus einem verschachtelten
Klassen-Pattern **nicht** in das Typargument von `Err` hinein: `case Err(A(...))` laesst als Rest
`Err[MyError]` statt `Never` stehen. Ueber einer **flachen** Union von Fehlerklassen rechnet `ty`
die Vollzaehligkeit dagegen aus. Der Ausweg ist deshalb nicht, das Muster zu verbiegen, sondern
den `Ok`/`Err`-Split gar nicht erst beim Aufrufer landen zu lassen.

## Die Entscheidung

`Result` bekommt seinen **Eliminator**. `Ok`/`Err` trugen bisher nur Operationen, die im `Result`
*bleiben* (`map`, `bind`, `map_err`, `or_else`, …) — keine, die kontrolliert herausfuehrt.

```python
def fold[U](self, on_ok: Callable[[T], U], on_err: Callable[[E], U], /) -> U: ...
```

Der Name ist `fold`, weil `.rules/python/python-feature-slices.md` und
[`2026-08-17-0937`](./2026-08-17-0937-pipeline-als-behavior-kette-im-shared-kernel.md) das Wort
fuer genau diese Stelle schon benutzen („ein Fold, kein Zweig", „**einen** Fold (`to_response`)").
Ein neuer Begriff daneben waere Drift.

Damit wird aus der Fundstelle:

```python
return outcome.fold(_accepted, _rejected)
```

`_rejected` matcht **flach** ueber die Fehler-Union, mit **einem** `assert_never` — der Fall, der
statisch durchprueft. Der `Ok`/`Err`-Split steht einmal in `result.py` statt an jeder Fundstelle.

## Der Einwand, und warum er nicht traegt

Das Repo argumentiert an zwei Stellen ausdruecklich **gegen** das Aufteilen der Response-Erzeugung:
`.rules/python/python-feature-slices.md` stellt „ein Fold, kein Zweig" gegen ein „Don't" mit zwei
Folds, und [`2026-08-17-0937`](./2026-08-17-0937-pipeline-als-behavior-kette-im-shared-kernel.md)
haelt fest, der Slice habe **einen** Fold. Ein `fold` mit zwei Callables sieht auf den ersten
Blick nach genau der verbotenen Aufteilung aus.

Er ist es nicht. Was die Regel verbietet, ist etwas anderes:

> Zwei Fehlerkanaele erzwingen zwei Folds in **dieselbe** Response-Union; der zweite Fold sieht
> dadurch nur Faelle, die der erste nicht schon abgefangen hat, und muss trotzdem alle behandeln.

Gemeint sind **zwei Eintrittspunkte** in die Response-Union, jeder mit unvollstaendiger Sicht.
`outcome.fold(_accepted, _rejected)` ist **ein** Aufruf an **einer** Stelle. Seine beiden Arme
sind seine Faelle — dasselbe, was vorher die beiden `case`-Zweige desselben `match` waren. Kein
Arm sieht weniger als vorher, kein zweiter Kanal entsteht, die Zahl der Eintrittspunkte in
`RegisterUserResponse` bleibt **eins**. Die Aufteilung ist lexikalisch, nicht strukturell.

Der Test `tests/contexts/identity/test_register_user_error_channel.py` misst das weiterhin
maschinell; er liest die Arme jetzt aus dem **Modul** von `to_response` statt aus der Funktion
allein, weil sie eine Ebene tiefer stehen. Was er zusichert, ist unveraendert: kein Fall von
`RegisterUserError` erreicht den Fold ohne Arm.

## Was daran haengt

- `src/contexts/shared_kernel/result.py` — der Eliminator, auf `Ok` **und** `Err`.
- `tests/test_result.py` — `TestFold`.
- `src/contexts/identity/application/register_user/mappers/register_user_response_mapper.py` —
  erste Fundstelle, umgestellt.
- `tests/contexts/identity/test_register_user_error_channel.py` — liest das Modul statt der
  Funktion.
- `src/contexts/identity/application/register_user/validators/register_user_rules.py` — die
  restlichen fuenf Fundstellen, umgestellt.

Jede Fundstelle des zweistufigen `match` traegt jetzt den Fold. In den Regeln fiel dabei auch die
Doppelung weg: statt fuenfmal `case Ok(): return []` gibt es **einen** Erfolgs-Arm `_no_errors`, und jeder
Fehler-Arm ist eine eigene, gegen ihre Union getypte Funktion (`_email_errors`,
`_password_errors`, …), die flach matcht. `ty` rechnet die Vollzaehligkeit dort aus, ohne dass
`pyproject.toml` einen `[[tool.ty.overrides]]`-Block braucht.

## Was gilt weiter

Die Regel „jeder `match` ist vollstaendig, der letzte Zweig wirft oder ruft `assert_never`"
([`2026-08-07-1120`](./2026-08-07-1120-jeder-match-endet-mit-assert-never.md)) ist unberuehrt.
`fold` ersetzt nicht `match`, sondern nimmt ihm die **aeussere** Stufe ab — die, die `ty` ohnehin
nicht ausrechnen konnte.
