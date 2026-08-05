# Python Async Patterns

> Uebersetzt `csharp-async.md` sinngemaess. Zielstack: **uv** + **ruff**
> (inkl. `ANN`-Regeln fuer vollstaendige Typannotationen). Kein mypy/pyright.

## No Blocking

Niemals eine Coroutine synchron "abwarten" (`asyncio.run()` innerhalb eines bereits laufenden
Loops, oder ein blockierender Aufruf wie `time.sleep`/`requests.get` in einer `async def`).
Immer `await`.

Do:
```python
async def process_order(order_id: OrderId) -> Order:
    order = await repository.get(order_id)
    await handler.handle(order)
    return order
```

Don't:
```python
def process(order_id: OrderId) -> Order:
    return asyncio.get_event_loop().run_until_complete(repository.get(order_id))  # Deadlock-Risiko
```

## Cancellation fliesst nativ mit — kein manuell durchgereichtes Token

C# muss ein `CancellationToken` explizit durch jede Signatur reichen, weil es keine eingebaute
Propagation gibt. `asyncio` hat diese Propagation bereits eingebaut: `Task.cancel()` wirft an der
naechsten `await`-Stelle automatisch `asyncio.CancelledError`. Ein eigenes "Cancellation-Token"-
Objekt nachzubauen und durch jede Funktion zu reichen waere eine unnoetige Nachbildung eines
Mechanismus, den die Sprache schon hat.

Nutze stattdessen strukturierte Nebenlaeufigkeit: `asyncio.TaskGroup` fuer parallele Kindaufgaben
und `asyncio.timeout()` fuer Fristen — beide sorgen dafuer, dass Abbruch automatisch an alle
laufenden `await`s innerhalb ihres Scopes propagiert wird.

Do:
```python
async def save(order: Order) -> None:
    async with asyncio.timeout(30):
        await db.save_changes(order)
        await notifier.notify(order)
```

Don't:
```python
async def save(order: Order, cancel_event: asyncio.Event) -> None:
    if cancel_event.is_set():          # manuell nachgebautes Cancellation-Token
        return
    await db.save_changes(order)
```

`CancelledError` faengt man nur an der einen Stelle, die eine definierte Aufraeum-Aktion braucht
(z. B. eine Ressource schliessen) — und reicht sie danach mit `raise` weiter. Sie zu schlucken
bricht die Propagation und ist das Python-Aequivalent zu C#s "dropped cancellation".

## async/await statt manueller Callback-/Future-Verkettung

Nutze `async`/`await` statt `.add_done_callback()`-Ketten oder manuelles Future-Chaining.

Do:
```python
async def process(request: OrderRequest) -> Order:
    await validator.validate(request)
    return await factory.create(request)
```

Don't:
```python
def process(request: OrderRequest) -> asyncio.Future[Order]:
    future = validator.validate(request)
    future.add_done_callback(lambda _: factory.create(request))
    return future
```

## Scopes statt Dispose

Wo C# ein `using CancellationTokenSource` fordert, nutzt Python fuer zeitlich begrenzte
Nebenlaeufigkeit einen `async with`-Kontextmanager (`asyncio.timeout`, `asyncio.TaskGroup`) —
die Bereinigung passiert deterministisch beim Verlassen des Blocks, kein manuelles Dispose noetig.

Do:
```python
async def get_with_deadline(order_id: OrderId) -> Order:
    async with asyncio.timeout(30):
        return await repository.get(order_id)
```
