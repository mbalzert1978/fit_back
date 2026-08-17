# Die Pipeline ist eine Behavior-Kette im Shared Kernel

**Datum:** 2026-08-17, 09:37
**Anlass:** Stufe 4 von Ticket [#51](https://github.com/mbalzert1978/fit_back/issues/51).

## Was entschieden wurde

`src/contexts/shared_kernel/pipeline.py` (nur stdlib) traegt drei Bausteine:

```python
type Handler[TIn, TOut, E] = Callable[[TIn], Awaitable[Result[TOut, E]]]
type Behavior[TIn, TOut, E] = Callable[[TIn, Handler[TIn, TOut, E]], Awaitable[Result[TOut, E]]]


def build_pipeline[TIn, TOut, E](handler, *behaviors) -> Handler[TIn, TOut, E]: ...
def validating[TIn, TOut, E](rule: AsyncRule[TIn], on_invalid) -> Behavior[TIn, TOut, E]: ...
```

Das **erste** Behavior liegt aussen; ein Behavior, das `Err` liefert, ohne den naechsten Schritt zu
rufen, laesst den Handler nicht laufen. Beides ist in `tests/test_pipeline.py` belegt, weil beides
an der Signatur nicht abzulesen ist.

Der Referenz-Slice `register_user` haengt genau ein Behavior in die Kette — die
Eingabe-Validierung — und hat danach **einen** gemeinsamen Fehlertyp (`RegisterUserError =
RequestInvalid | EmailAlreadyRegistered`) und **einen** Fold (`to_response`, drei erreichbare Arme
plus `assert_never`).

## Warum das und nicht der Wrapper mit `if`

Vorher stand in `RegisterUserPipeline.run` eine imperative Verzweigung ueber zwei Fehlerkanaele
(`list[FieldError]` und `DomainError`) mit zwei Folds in **dieselbe** Response-Union. Daraus folgte
alles Weitere: der zweite Fold sah nur, was der erste nicht schon abgefangen hatte, musste aber
trotzdem alle Faelle behandeln — und Querschnittliches (Transaktionsklammer, Idempotenz, Messung,
Logging) hatte keinen Ort ausser „ein Absatz mehr in `run`".

## Was daran haengt

- **`Result.bind_async`** (`Ok`/`Err`). Ohne sie laesst sich ein `async` Handler nicht verketten —
  genau deshalb stand dort ein `if`. Sie ist die Abkuerzung, von der `validating` lebt: auf `Err`
  wird die Fortsetzung gar nicht erst erzeugt.
- **`AsyncRule[T]` / `all_of_async` / `as_async`** in `validation.py`. `validating` nimmt die
  asynchrone Regelform, damit eine Regel mit IO ueberhaupt eine Regel sein kann; die vorhandenen
  synchronen Regeln des Slice werden beim Verdrahten mit `as_async` gehoben, statt sie ohne Not
  `async` zu schreiben.
- **`validation.py` wird nicht ersetzt.** `Rule`, `all_of`, `FieldError` bleiben, wo sie sind;
  `pipeline.py` weiss, *wann* validiert wird, nicht *was* gilt.

## Bewusst nicht gebaut

- **Kein zweites Behavior auf Vorrat.** Logging, Transaktionsklammer, Idempotenz und Messung sind
  in der Kette moeglich; gebaut werden sie, wenn sie gebraucht werden.
- **`all_of_async` hat heute keinen Produktionsaufrufer** — es ist die Komposition, ohne die
  `AsyncRule` als Regelform nicht vollstaendig waere, und ist in `tests/test_pipeline.py` gedeckt.
  Das ist die eine bewusst in Kauf genommene Vorwegnahme dieser Stufe; sie steht so im Ticket.
- **Kein `CancellationToken`-Aequivalent.** `asyncio` propagiert den Abbruch ueber `CancelledError`
  ([`.rules/python/python-async.md`](../../.rules/python/python-async.md)).
