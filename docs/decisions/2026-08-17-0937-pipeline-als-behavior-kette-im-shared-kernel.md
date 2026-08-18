# Die Pipeline ist eine Behavior-Kette im Shared Kernel

**Datum:** 2026-08-17, 09:37
**Anlass:** Stufe 4 von Ticket [#51](https://github.com/mbalzert1978/fit_back/issues/51).

## Was entschieden wurde

`src/contexts/shared_kernel/pipeline.py` (nur stdlib) traegt **die Naht und sonst nichts**:

```python
type Handler[TIn, TOut, E] = Callable[[TIn], Awaitable[Result[TOut, E]]]
type Behavior[TIn, TOut, E] = Callable[[TIn, Handler[TIn, TOut, E]], Awaitable[Result[TOut, E]]]


def build_pipeline[TIn, TOut, E](handler, *behaviors) -> Handler[TIn, TOut, E]: ...
```

Jedes **konkrete** Behavior liegt in einer eigenen Einheit unter
`src/contexts/shared_kernel/behaviors/` und haengt von der Naht ab, nicht umgekehrt — heute genau
eines:

```python
# behaviors/validating.py
def validating[TIn, TOut, E](rule: AsyncRule[TIn], on_invalid) -> Behavior[TIn, TOut, E]: ...
```

Die Trennung ist die Antwort auf die Frage, wo das **zweite** Querschnitts-Behavior hingehoert: als
Nachbarmodul in `behaviors/`. Bliebe es bei einer Datei, aenderte sich die Naht — die alle teilen —
jedes Mal mit, wenn ein einzelnes Behavior dazukommt, und zoege dessen Abhaengigkeiten
(`validating` braucht `validation.py`) fuer alle mit herein.

Das **erste** Behavior liegt aussen; ein Behavior, das `Err` liefert, ohne den naechsten Schritt zu
rufen, laesst den Handler nicht laufen. Beides ist in `tests/test_pipeline.py` belegt, weil beides
an der Signatur nicht abzulesen ist; das Validierungs-Behavior in
`tests/test_validating_behavior.py`.

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
  `behaviors/validating.py` weiss, *wann* validiert wird, nicht *was* gilt — und `pipeline.py`
  weiss von beidem nichts.

## Bewusst nicht gebaut

- **Kein zweites Behavior auf Vorrat.** Logging, Transaktionsklammer, Idempotenz und Messung sind
  in der Kette moeglich; gebaut werden sie, wenn sie gebraucht werden.
- **`all_of_async` hat heute keinen Produktionsaufrufer** — es ist die Komposition, ohne die
  `AsyncRule` als Regelform nicht vollstaendig waere, und ist in `tests/test_pipeline.py` gedeckt.
  Das ist die eine bewusst in Kauf genommene Vorwegnahme dieser Stufe; sie steht so im Ticket.
- **Kein `CancellationToken`-Aequivalent.** `asyncio` propagiert den Abbruch ueber `CancelledError`
  ([`.rules/python/python-async.md`](../../.rules/python/python-async.md)).
