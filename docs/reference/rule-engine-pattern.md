# Rule Engine Pattern (C#) — Lesenotiz und Abgleich

**Quelle:** [The Modern Way to Manage C# Business Rules: Rule Engine Pattern](https://senrecep.medium.com/the-modern-way-to-manage-c-business-rules-rule-engine-pattern-14bb1c72d700)
(senrecep, Medium). Begleitcode: NuGet `CSharpEssentials`, GitHub `senrecep/CSharpEssentials`.
**Gelesen:** 2026-08-07. **Status:** nichts uebernommen — drei Vorschlaege am Ende, alle offen.

Bezug: [`.rules/python/python-rule-pattern.md`](../../.rules/python/python-rule-pattern.md), das
bereits den [Rule-Pattern-Artikel](https://dev.to/stevsharp/the-rule-pattern-in-c-2ed0) desselben
Themenkreises zitiert. Dieser Artikel geht einen Schritt weiter: vom *Muster* zur *Engine*.

## Was der Artikel beschreibt

**Problem.** Geschaeftsregeln liegen verstreut und doppelt im Code, die Fehlerbehandlung ist
uneinheitlich, und weil die Regeln mit der Fachlogik verwoben sind, sinkt die Testbarkeit.

**Result statt Exceptions.** Rueckgabe ist `Result.Success()` oder ein `Error` mit Code,
Beschreibung und optionalen Metadaten (`ErrorMetadata` als Schluessel-Wert-Paare). Fehlerpfade
werden damit explizit statt zu Kontrollfluss ueber Ausnahmen.

**Regel-Schnittstellen.**

| Schnittstelle | Bedeutung |
|---|---|
| `IRule<TContext>` / `IAsyncRule<TContext>` | eine Regel, eine Frage |
| `ILinearRule<TContext>` | Kette; stoppt beim ersten Fehler (`IRuleBase<T>? Next`) |
| `IAndRule<TContext>` | alle muessen passen, Fehler werden gesammelt |
| `IOrRule<TContext>` | mindestens eine muss passen |
| `IConditionalRule<TContext>` | If/Else ueber `Success`/`Failure`-Properties |

```csharp
internal readonly record struct AdultRule : IRule<User> {
    public Result Evaluate(User context) =>
        context.Age >= 18 ? Result.Success() : Error.Validation(...);
}
```

Der Autor empfiehlt ausdruecklich `readonly record struct` — Wert-Semantik, Unveraenderlichkeit,
Thread-Sicherheit, keine Heap-Allokation.

**Komposition** in zwei Stilen. Objektorientiert ueber eine Regel, die andere Regeln aufzaehlt:

```csharp
public readonly record struct OrderValidationRule : IAndRule<Order> {
    public IRuleBase<Order>[] Rules => [
        new OrderAmountRule(...), new StockAvailabilityRule(...), new PaymentMethodValidationRule(...)
    ];
}
```

oder funktional: `RuleEngine.And(rules: [UserRules.ActiveCheck, UserRules.AdultCheck], context: user)`
mit den Signaturen `Func<TContext, Result>` bzw. `Func<TContext, CancellationToken, ValueTask<Result>>`.

**Fehler zentral je Entitaet:**

```csharp
internal static class UserErrors {
    public static Error NotAdult => Error.Validation(code: "USER.NOT_ADULT", description: "...");
}
```

**Abhaengigkeiten** kommen ueber den Konstruktor in die Regel
(`new CreditApplicationRule(creditScoreService, blacklistService)`), **Async** ueber eigene
Schnittstellen (`IAsyncRule<T>`, `ILinearAsyncRule<T>`) mit `CancellationToken`.

**Unterschied zum einfachen Rule Pattern.** Dort ist eine Regel ein Objekt mit `IsSatisfied()` /
`Validate()`. Die Engine ergaenzt **Kombinatoren** (AND/OR/Linear/Conditional), aus denen sich
Validierungs-*Baeume* aus atomaren Regeln bauen lassen.

**Vorteile laut Autor:** Zentralisierung je Entitaet, einheitliche Fehlerbehandlung, gute
Testbarkeit der Einzelregel, geringe Allokation, Komponierbarkeit, kein Ausnahme-Overhead.
Nachteile nennt der Artikel keine; implizit erkauft man sie mit mehr Gerüst und einer Lernkurve.

## Abgleich: was davon steht hier schon

Der groesste Teil. Die Spalte rechts ist kein „aehnlich", sondern die gebaute Entsprechung.

| Artikel | in diesem Repo |
|---|---|
| `Result` statt Exceptions | [`shared_kernel/result.py`](../../src/contexts/shared_kernel/result.py) — `Ok[T]`/`Err[E]`, PEP-695-generisch |
| Fehler traegt Code + Metadaten | Tagged-Union-Fall mit `code: ClassVar[str]` und typisierter Nutzlast; `FieldError(field, error_code, parameters)` |
| Fehler zentral je Entitaet | `domain/<vo>_errors.py` je Value Object, zusammengefuehrt in `domain/errors.py` |
| Regel = feste Signatur | `type Rule[T] = Callable[[T], list[FieldError]]` in [`validation.py`](../../src/contexts/shared_kernel/validation.py) |
| `IAndRule` — alle laufen, sammeln | `all_of(*rules)` |
| `ILinearRule` — erster Fehler gewinnt | `chain(*rules)` ueber `Result.bind` |
| verschachtelte Komposition | `all_of` liefert selbst ein `Rule[T]` — Baeume gehen schon heute |
| `readonly record struct` | `@dataclass(frozen=True, slots=True)` |
| Abhaengigkeit in die Regel | Closure statt Konstruktor: `email_rule(idn)` |
| Regel testet sich einzeln | jede Regel ist eine gewoehnliche Funktion |

**An einer Stelle sind wir strenger, und das absichtlich.** Der `Error` des Artikels traegt eine
`description` — Prosa im Fehlerobjekt. Hier ist genau das verboten: der Fall traegt Code und
typisierte Nutzlast, der Text entsteht erst am HTTP-Rand nach `Accept-Language`
([`2026-08-07-0634`](../decisions/2026-08-07-0634-fehlercodes-statt-prosa-aus-dem-slice.md),
[`-0646`](../decisions/2026-08-07-0646-fehlernutzlast-als-typisierter-fall-ist-regel.md)). Eine `description`
waere ein zweiter, unuebersetzbarer Kanal daneben.

## Was tatsaechlich fehlt

Drei Dinge, und nur drei:

1. **`IOrRule` — „mindestens eine muss passen".** Es gibt kein `any_of`. Heute gibt es im Repo
   auch keinen Fall dafuer; klassisch waere „E-Mail **oder** Telefonnummer muss angegeben sein".
2. **`IConditionalRule` — If/Else ueber Regeln.**
3. **Async-Regeln.** `Rule[T]` ist synchron. Eine Regel, die IO braucht (Nachschlagen in einer
   Referenzliste, Aufruf eines fremden Context ueber einen Port), laesst sich heute nicht als
   Regel formulieren.

## Vorschlaege — offen, nicht entschieden

Keiner davon ist umgesetzt, und `.rules/python/python-rule-pattern.md` ist unveraendert.

**1. Async-Regeln — dafuer, aber gebunden an Ticket 0011 Stufe 4.**
Das ist die einzige der drei Luecken mit einem konkreten Anlass. Stufe 4 baut ohnehin
`bind_async` und die Behavior-Kette; eine asynchrone Regelform gehoert in denselben Schnitt statt
davor. Sie jetzt einzeln zu bauen, hiesse sie zweimal anzufassen.

**2. `any_of` (OR) — dagegen, bis ein echter Fall auftaucht.**
Es gibt heute keinen. Ein Kombinator auf Vorrat widerspricht
[`exp_kein-vorauseilendes-shared.md`](../reflections/exp_kein-vorauseilendes-shared.md) — und OR
hat eine Frage offen, die sich ohne konkreten Fall nicht beantworten laesst: **welchen** Fehler
meldet man, wenn alle Zweige scheitern? Alle? Den ersten? Einen eigenen? Diese Entscheidung will
am Anwendungsfall getroffen werden, nicht am leeren Tisch.

**3. `IConditionalRule` — dagegen.**
Ein `if` in einer gewoehnlichen Regel-Funktion ist lesbarer als ein Kombinator, der dasselbe
ausdrueckt. Der Artikel braucht ihn, weil in C# die Regel ein *Objekt* ist und Ablauflogik dort
nur als Struktur ausdrueckbar ist. Hier ist die Regel eine Funktion — sie darf verzweigen.

**Ausdruecklich nicht uebernehmen:**

- **`Error.description`** — siehe oben, widerspricht der Codes-statt-Prosa-Entscheidung.
- **Regel-Objekte mit Schnittstellen** (`IRule<T>`, `IRuleBase<T>`). Der Artikel bietet den
  funktionalen Stil selbst an, und `python-rule-pattern.md` verbietet ausdruecklich, `Rule` als
  feature-lokale `Protocol`-Klasse nachzubauen. In Python **ist** die Funktion die Regel.
- **`CancellationToken`** — asyncio bringt Cancellation ueber `CancelledError` mit; ein
  durchgereichter Token waere ein Fremdkoerper.
