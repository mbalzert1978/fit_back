---
schema_version: 1
name: kovarianz-braucht-final-nicht-frozen
description: Bei PEP-695-Generics zaehlt `frozen=True` fuer die Varianzrechnung nicht - erst `Final[T]` am Feld macht den Typparameter kovariant, und ein Typparameter in einer Continuation-Signatur steht kontravariant
type: project
frequency: 1
last_triggered: 2026-08-26
decay_eligible: true
---

Ein generischer Ergebnistyp (`Result[T, E]`, `Maybe[T]`, …) ist nur dann kovariant, wenn **beides**
stimmt:

1. Das tragende Feld ist als `Final[T]` deklariert. `@dataclass(frozen=True)` allein reicht nicht —
   die Varianzrechnung sieht ein gewoehnliches, beschreibbares Attribut und schliesst auf invariant.
2. Kein Klassen-Typparameter steht in **kontravarianter** Position. In den durchreichenden
   Methoden (`Ok.or_else`, `Err.bind`, `Err.bind_async`) darf der Callback-Parameter nicht den
   Klassenparameter nennen; dort gehoeren eigene Methoden-Typparameter hin.

**Why:** Sieben `invalid-return-type`-Befunde in sieben Dateien — `parse`-Methoden von sechs Value
Objects und die `register_user`-Pipeline — hatten genau diese eine Ursache: `Err[EmailAlreadyRegistered]`
passte nicht in `Err[RegisterUserError]`. Die eingetragene Baseline-Begruendung hatte eine
Werkzeug-Luecke vermutet. Beide Aenderungen zusammen sind noetig, per Bisektion belegt: einzeln
raeumt keine die Befunde ab. Als sie standen, wurde die Pipeline still, **ohne angefasst zu
werden**. Hergang: `docs/decisions/2026-08-25-1500-typechecker-ty.md`, Welle 1.

**How to apply:** Bei jedem neuen oder geaenderten generischen Traeger-Typ im Shared Kernel: Felder
`Final[T]`, und in jeder Methode, die den Wert unveraendert durchreicht, die Callback-Typen als
eigene Methoden-Parameter fuehren. Symptom, an dem man es erkennt: der Typpruefer meldet an
**vielen** Aufrufstellen dasselbe Zuweisungsproblem mit einem Subtyp im Typargument — dann liegt
die Ursache in der Definition des Generics, nicht an den Aufrufstellen. Nicht die Aufrufstellen
einzeln reparieren.
