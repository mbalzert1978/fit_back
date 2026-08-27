# Docstrings bestehen den Streichtest

## Was entschieden wurde

Zwei Regeln, festgehalten in
[`.rules/common/docstrings-und-kommentare.md`](../../.rules/common/docstrings-und-kommentare.md):

1. **Ein Docstring sagt, was die Signatur nicht sagen kann.** Streichtest: Wäre der Satz auch nach
   dem Löschen noch wahr, gehört er gelöscht.
2. **Ein Kommentar erklärt WARUM, nie WAS.** Erklärt er, *was* der Code tut, ist der Code der
   Befund.

## Der Anlass

Aufgefallen an einer Stelle, die in dieser Sitzung entstanden ist:

```python
def inspect_async[E](self, f: Callable[[T], Awaitable[_Unit]], /) -> AsyncResult[T, E]:
    """Loese eine Nebenwirkung auf dem Erfolgs-Wert aus, ohne die Kette zu aendern.

    Waere der Rueckgabewert von `f` von Belang, waere `bind` das Werkzeug.
    """
```

Der zweite Satz beantwortet „warum nicht `bind`?". Das ist die Frage eines Reviewers, nicht die
eines Aufrufers. Die Signatur sagt bereits alles, was der Aufrufer braucht: `_Unit` hinein heißt,
der Wert wird verworfen; `AsyncResult[T, E]` heraus heißt, die Kette bleibt unverändert.

## Warum es überhaupt so weit kam

Drei Ursachen, alle drei ohne Gegenkraft:

- **Ein Docstring als Verteidigung geschrieben, nicht als Hilfe.** Wer eine Entwurfsentscheidung
  gegen einen gedachten Einwand absichert, schreibt einen Absatz, den nie jemand braucht, der die
  API nur benutzen will.
- **Anpassung an die Umgebung.** Neben einem langen Docstring entsteht ein längerer. Das ist eine
  Ratsche und keine Entscheidung — sie läuft nur in eine Richtung.
- **Kein Werkzeug bremst.** Ruff prüft mit den `D`-Regeln, **ob** ein Docstring existiert, nie wie
  lang er ist. Es gab bis hierher auch keine Regel in `.rules/`.

## Was ersetzt wird

Nichts wird ungültig — die Regel ist neu, nicht korrigierend. Sie steht in `common/`, weil sie
sprachunabhängig gilt; Ruffs `D`-Regeln bleiben unverändert, sie beantworten eine andere Frage.

Begründungen für Entwurfsentscheidungen gehören weiterhin ausschließlich hierher, nach
[`docs/decisions/`](.), und die destillierten Lektionen nach
[`docs/reflections/`](../reflections/). Neu ist nur die Aussage, dass sie **nicht zusätzlich** in
den Docstring gehören: eine zweite Kopie driftet. Ein Verweis ist erlaubt, eine Wiederholung nicht.

## Was daran nicht selbsttragend ist

Der Streichtest ist eine Urteilsfrage und maschinell nicht prüfbar. Ruff kann Länge nicht bewerten,
und eine Zeilenobergrenze wäre die falsche Antwort — ein langer Docstring über einer echten
Vorbedingung ist richtig, ein kurzer über einer Selbstverständlichkeit falsch.

Getragen wird die Regel deshalb vom Review, gestützt auf den `verifier-comments`-Check aus der
Skill-Bibliothek.

## Der Durchgang über den Bestand

Nachgezogen in `4bab149`: 61 Dateien, 501 gestrichene gegen 129 neue Zeilen. Je ein Agent pro
Ordner, rekursiv von oben.

Was dabei zutage kam, schärft die Regel:

- **Refactoring-Geschichte war der häufigste Befund.** Sätze wie „vorher stand das im Router" oder
  „waren acht Argumente, bevor …" erzählen einem Aufrufer nichts. Sie stehen im Log.
- **Sieben Fehler-Dateien in `identity` trugen denselben Satz wortgleich.** Genau die zweite Kopie,
  vor der der Abschnitt oben warnt — nur eben siebenfach.
- **`src/contexts/shared_kernel/result.py` war wie erwartet der dichteste Fall** und verlor allein
  91 Zeilen.
- **`alembic/versions/` blieb unberührt.** In einer Migration ist der Kommentar oft das einzige
  Zeugnis einer Umzugsentscheidung; der Kopf-Docstring gehört ohnehin Alembic.

Ein Verweis ersetzt die gestrichene Begründung nur dort, wo ihr Verlust den Code gefährdet — etwa
bei `AsyncResult.zip_all`, wo das freie `V` wie eine überflüssige Verkomplizierung aussieht und eine
„Vereinfachung" zu `T` den Typcheck bräche.
