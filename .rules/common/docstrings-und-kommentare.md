# Docstrings und Kommentare

Zwei Regeln. Beide sind Streichtests, keine Stilfragen.

## 1. Ein Docstring sagt, was die Signatur nicht sagen kann

**Streichtest:** Wäre der Satz auch nach dem Löschen noch wahr — weil Name, Parameter, Typen und
Rückgabe ihn schon tragen —, gehört er gelöscht.

Wer die API benutzt, liest die API. Namen und Typen sind die Dokumentation; ein Docstring ergänzt
nur, was dort nicht hineinpasst: eine Vorbedingung, eine Reihenfolge, eine Einheit, eine
Nebenwirkung, ein Fall, in dem die Methode etwas *nicht* tut.

Don't:
```python
def inspect_async[E](self, f: Callable[[T], Awaitable[_Unit]], /) -> AsyncResult[T, E]:
    """Loese eine Nebenwirkung auf dem Erfolgs-Wert aus, ohne die Kette zu aendern.

    Waere der Rueckgabewert von `f` von Belang, waere `bind` das Werkzeug.
    """
```

Der zweite Satz beantwortet „warum nicht `bind`?" — eine Frage des Reviewers, nicht des Aufrufers.
`_Unit` rein und `AsyncResult[T, E]` raus sagt bereits: der Wert wird verworfen, die Kette bleibt.

Do:
```python
def inspect_async[E](self, f: Callable[[T], Awaitable[_Unit]], /) -> AsyncResult[T, E]:
    """Loese eine Nebenwirkung auf dem Erfolgs-Wert aus."""
```

## 2. Ein Kommentar erklärt WARUM, nie WAS

Erklärt ein Kommentar, *was* der Code tut, ist der Code der Befund — nicht der fehlende Kommentar.
Die Antwort ist ein besserer Name, eine extrahierte Funktion oder eine Zusicherung, nicht ein Satz
daneben.

Bleiben darf ein Kommentar, wenn er etwas trägt, das im Code nicht steht: eine externe Vorgabe,
einen Messwert, eine bewusst nicht gewählte Alternative, eine Fremdsystem-Eigenart.

## Wo Begründungen stattdessen hingehören

Der Grund für eine Entwurfsentscheidung gehört nach [`docs/decisions/`](../../docs/decisions/), die
destillierte Lektion nach [`docs/reflections/`](../../docs/reflections/). Steht sie zusätzlich im
Docstring, ist sie eine zweite Kopie — und Kopien driften.

Ein Docstring darf auf eine Entscheidung **verweisen**. Er wiederholt sie nicht.

## Warum das eine Regel braucht

Nichts bremst hier von allein. Ruff prüft mit den `D`-Regeln nur, **ob** ein Docstring da ist, nie
wie lang er ist. Und wer sich an die Umgebung anpasst, schreibt neben einem langen Docstring einen
längeren — eine Ratsche, die nur in eine Richtung läuft.

## Review-Checkliste

- [ ] Jeder Satz im Docstring besteht den Streichtest: er sagt etwas, das Name, Parameter, Typen und
      Rückgabe nicht schon sagen.
- [ ] Keine Entwurfsbegründung im Docstring, die in `docs/decisions/` bereits steht — höchstens ein
      Verweis darauf.
- [ ] Kein Kommentar, der beschreibt, *was* die nächste Zeile tut.
- [ ] Ein Docstring, der die Umgebung nur nachahmt, weil dort schon lange Docstrings stehen, ist
      kein Argument für einen langen Docstring.
