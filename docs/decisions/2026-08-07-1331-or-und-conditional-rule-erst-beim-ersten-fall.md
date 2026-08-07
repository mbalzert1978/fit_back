# `any_of` (OR) und Conditional Rule kommen erst beim ersten echten Fall

**Datum:** 2026-08-07, 13:31
**Status:** entschieden — nicht gebaut, bewusst

## Der Anlass

Der [Rule-Engine-Artikel](../reference/rule-engine-pattern.md) beschreibt vier Kombinatoren:
AND, Linear, **OR** und **Conditional**. Die ersten beiden sind hier gebaut (`all_of`, `chain`),
die letzten beiden fehlen. Die Frage war, ob sie nachgezogen werden.

## Die Entscheidung

**Beide werden nicht gebaut, solange kein Anwendungsfall im Repo existiert** — YAGNI, konsistent
mit [`exp_kein-vorauseilendes-shared.md`](../reflections/exp_kein-vorauseilendes-shared.md).

Diese Datei existiert, damit die Frage beim ersten echten Fall **nicht neu aufgerollt** werden
muss: die Analyse steht hier, es fehlt dann nur noch die eine offene Antwort.

## `any_of` (OR) — was beim Bauen zu klaeren ist

Der Kombinator selbst ist trivial. Die Entscheidung, die ihn schwierig macht, ist eine einzige:

> **Welchen Fehler meldet OR, wenn *alle* Zweige scheitern?**

Drei Antworten sind vertretbar, und sie sind nicht gleichwertig:

| Antwort | Folge |
|---|---|
| **alle** Fehler sammeln | Der Aufrufer bekommt widerspruechliche Auskuenfte („E-Mail ist ungueltig" *und* „Telefonnummer ist ungueltig"), obwohl er nur **eines** von beidem liefern musste. |
| den **ersten** melden | Willkuerlich — die Reihenfolge der Regeln wird zur fachlichen Aussage, ohne dass das jemand entschieden hat. |
| einen **eigenen** Fall melden | Ehrlich („mindestens eines von *email*, *phone* wird gebraucht"), verlangt aber je OR-Gruppe einen eigenen Fehlerfall mit eigenem Code und eigener Textvorlage. |

Die dritte Antwort ist die einzige, die dem Aufrufer sagt, was er tun soll — sie ist aber auch die
einzige, die **nicht** vom Kombinator allein geleistet werden kann: er braucht den Fehlerfall von
aussen. Eine plausible Signatur waere deshalb

```python
def any_of[T](*rules: Rule[T], sonst: FieldError) -> Rule[T]: ...
```

— aber ob `sonst` ein Wert, eine Fabrik oder ein eigener Regel-Parameter ist, entscheidet der
erste echte Fall. **Vorher ist jede Wahl geraten.**

Ein weiterer Punkt, der erst am Fall entscheidbar ist: OR ueber Felder **verschiedener** Namen
(`email` oder `phone`) hat kein natuerliches `field` fuer den Fehler. Vermutlich gehoert er dann
an den Body als Ganzes, wie `BodyNotAnObject` heute.

## Conditional Rule — abgelehnt, nicht aufgeschoben

Anders als OR ist das keine Terminfrage, sondern eine Absage.

Der Artikel braucht `IConditionalRule<TContext>` mit `Success`/`Failure`-Properties, **weil dort
eine Regel ein Objekt ist**: Ablauflogik laesst sich in C# an dieser Stelle nur als Struktur
ausdruecken. Hier ist eine Regel eine gewoehnliche Funktion mit der Signatur
`Callable[[T], list[FieldError]]` — sie darf verzweigen:

```python
def zeitzone_nur_bei_eigenem_profil(request: ProfilRequest) -> list[FieldError]:
    if not request.eigenes_profil:
        return []
    return time_zone_must_be_known(request)
```

Ein Kombinator, der dasselbe ausdrueckt, waere eine Indirektion ohne Gewinn — und genau die Sorte
Zwischenschicht, die in `register_user_rules.py` schon einmal dazu gefuehrt hat, dass eine
Signatur bis zur Unwahrheit aufgemacht wurde
(`.rules/python/python-rule-pattern.md`, Review-Checkliste).

**Wird diese Absage je revidiert?** Nur, wenn eine Bedingung ueber *mehrere* Regeln hinweg
mehrfach identisch auftritt und das `if` dadurch dupliziert wird. Dann ist der Kombinator die
Antwort — aber dann auch aus einem gemessenen Grund, nicht aus dem Katalog.

## Was **nicht** aufgeschoben ist

**Async-Regeln** sind die dritte Luecke aus derselben Notiz und werden gebaut: sie haengen in
Ticket 0011, Stufe 4, weil dort `bind_async` und die Behavior-Kette ohnehin entstehen. Sie einzeln
davor zu bauen hiesse, sie zweimal anzufassen.

## Folgen

- `.rules/python/python-rule-pattern.md` bleibt unveraendert — es beschreibt weiterhin genau die
  zwei Varianten, die gebaut sind.
- [`docs/reference/rule-engine-pattern.md`](../reference/rule-engine-pattern.md) verweist auf diese
  Entscheidung, damit die Vorschlaege dort nicht als offen gelesen werden.
- Taucht ein OR-Fall auf, ist die Vorarbeit die Tabelle oben: nur noch **eine** Frage beantworten,
  dann bauen.
