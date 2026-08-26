# `AsyncResult`: die async-Kette bleibt bis zum Schluss chainbar

**Datum:** 2026-08-26, 15:00
**Status:** entschieden, umgesetzt

## Der Anlass

`Ok.bind_async` war bisher ein `async def` und lieferte damit eine **nackte Coroutine**. Auf einer
Coroutine gibt es kein `.map()`. Wer nach einem asynchronen Schritt weitermachen wollte, musste
zwischendurch `await`en — sichtbar im Slice:

```python
return await (await step(request)).bind_async(issue)  # src/.../session_step.py
```

Zwei `await` in einer Zeile, und das innere steht nur da, um an die naechste Methode zu kommen.
Gefordert war die Form, die C# ueber `Task<Result<…>>`-Erweiterungen erlaubt:

```csharp
await selfTask.MapAsync(v => v * 2).BindAsync(v => SomeFnReturningResult(v));
```

## Die Entscheidung

Ein zweiter Traeger neben `Ok`/`Err`, im **selben Modul**: `AsyncResult[T, E]` haelt ein
`Awaitable[Result[T, E]]` statt eines fertigen `Result`.

- Jede Kombinator-Methode gibt wieder ein `AsyncResult` zurueck — deshalb bleibt die Kette offen.
- `AsyncResult` ist selbst `await`-bar (`__await__`), deshalb steht **ein** `await` am Ende.
- Jede `_async`-Methode auf `Ok`/`Err` liefert nun ein `AsyncResult` statt einer Coroutine.

```python
await AsyncResult(self_task).map(lambda v: v * 2).bind_async(some_fn_returning_result)
```

**Keine zweite Result-Implementierung.** `AsyncResult` entscheidet nirgends selbst ueber den
Ausgang: jede Methode faltet ihr Awaitable auf und ruft die **gleichnamige** Methode auf `Ok`
bzw. `Err`. Damit ist auch der Kurzschluss derselbe — liegt ein `Err` vor, laeuft kein weiterer
Schritt an, belegt in `tests/test_async_result.py`.

**Nur stdlib.** Keine neue Abhaengigkeit; `AsyncResult` ist ein `@final`, frozen Dataclass ueber
`collections.abc.Awaitable`.

### Die Namensregel

Der Zusatz `_async` sagt, ob der **uebergebene Callable** asynchron ist — nicht, ob die Methode
selbst wartet. `map` nimmt `T -> U`, `map_async` nimmt `T -> Awaitable[U]`. Beide geben ein
`AsyncResult` zurueck, beide sind gleich chainbar. Eine Kette darf sync- und async-Schritte frei
mischen. Der Alternativentwurf — **eine** Methode, die beides annimmt (`U | Awaitable[U]`) und zur
Laufzeit `inspect.isawaitable` prueft — ist verworfen: er macht die Typinferenz mehrdeutig
(`U` koennte die Coroutine selbst sein) und bezahlt sie mit einer Laufzeit-Fallunterscheidung.

## Der Signaturwechsel, und warum er niemanden bricht

`Ok.bind_async`, `Err.bind_async`, `Ok.inspect_async` und `Err.inspect_async` liefern nicht mehr
`Coroutine[…, Result[…]]`, sondern `AsyncResult[…]`. Weil `AsyncResult` awaitable ist und dasselbe
`Result` liefert, laufen alle drei bestehenden Aufrufstellen unveraendert weiter:
`behaviors/validating.py`, `register_user/handler.py`, `register_user/session_step.py`. Die
**sync**-API (`map`, `bind`, `map_err`, `or_else`, `fold`) ist unberuehrt.

Zwei sync-Signaturen wurden **geweitet**, nicht geaendert: `Ok.or_else` und `Ok.or_else_async`
fuehrten den eingehenden und den ausgehenden Fehlertyp unter demselben Typparameter `F`. Das war
schon vorher zu eng — die Alternative darf einen *anderen* Fehler liefern — und machte die
Delegation aus `AsyncResult.or_else` unaufloesbar. Jetzt sind es zwei freie Parameter. Kein
bestehender Aufruf wird davon ungueltig.

## Die Varianz-Falle, die dabei aufschlug

Der erste Entwurf schrieb `AsyncResult.bind` als
`Callable[[T], Result[U, E]] -> AsyncResult[U, E]` — mit dem **Klassen**-Parameter `E` in der
Rueckgabe des uebergebenen Callables. Eine Methoden-Parameterposition ist kontravariant, die
Rueckgabe eines Callables kovariant; zusammen sitzt `E` damit **kontravariant**. `AsyncResult`
wurde invariant in `E` — und riss ueber `Err._settled()` die Kovarianz von `Err` selbst mit
herunter. `ty` meldete das prompt an drei ganz anderen Stellen (`pipeline.py`, `email.py`,
`user_time_zone.py`), wo `Err[UserTimeZoneUnknown]` ploetzlich nicht mehr als
`Err[UserTimeZoneError]` durchging.

Die Loesung ist dieselbe, die das Modul schon fuer `Err.bind` und `Ok.or_else` benutzt und in
seinem Docstring begruendet: **freie Typparameter**. `bind[U, F](f: Callable[[T], Result[U, F]])
-> AsyncResult[U, E | F]` haelt `E` in reiner Rueckgabeposition. Der Docstring des Moduls ist
entsprechend nachgezogen; er zaehlt die betroffenen Methoden nicht mehr einzeln auf, sondern nennt
die Regel dahinter.

Festgehalten, weil die Falle bei jeder weiteren Methode auf `Ok`/`Err`/`AsyncResult` erneut
zuschnappt: **kein Klassen-Typparameter in der Rueckgabe eines uebergebenen Callables.**

## Was daran haengt

- `src/contexts/shared_kernel/result.py` — `AsyncResult` und die `_async`-Arme auf `Ok`/`Err`.
- `src/contexts/shared_kernel/__init__.py` — `AsyncResult` exportiert.
- `tests/test_async_result.py` — 40 Tests; `result.py` steht bei 100 % Zeilenabdeckung.

Nachgezogen in einem eigenen Commit: `UserRegistry.add` liefert die Kette statt einer Coroutine,
und die drei Stellen, die deshalb zweimal warten mussten, kommen mit einem `await` aus —
`session_step.py`, `behaviors/validating.py` und `register_user/handler.py`.
