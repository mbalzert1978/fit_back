# Jeder `match` ist vollstaendig — Abschlusszweig wirft `assert_never`

**Datum:** 2026-08-07, 11:20
**Status:** entschieden, umgesetzt

## Der Anlass

Beim Aufraeumen des Response-Mappers von `register_user` (Ticket 0008) fiel auf, dass eine
Begruendung, die dieses Repo an mehreren Stellen fuehrt, schlicht nicht stimmt. Sie stand so im
Docstring von `to_response` und so auch in `.rules/python/python-error-handling.md`:

> Vollstaendiges Matching ohne Auffangzweig: waechst `DomainError` um einen Fall, faellt genau hier
> auf, dass die Antwort dafuer noch fehlt.

Das faellt nicht auf. **Python erzwingt die Vollzaehligkeit eines `match` zur Laufzeit nicht.**
Passt kein Zweig, faellt der `match` still durch; eine Funktion mit Rueckgabewert liefert dann
`None`. Der Fehler taucht irgendwo weiter oben als `AttributeError` auf einem `NoneType` auf, weit
weg von seiner Ursache — und im schlechtesten Fall gar nicht, sondern als fehlendes Feld in einer
Antwort.

In C# uebernimmt das der Compiler, und der uebliche Abschluss ist
`_ => throw new UnreachableException()`. Dieses Repo faehrt bewusst ohne Typpruefer (derselbe Grund,
aus dem `CodedError` ein `@runtime_checkable` Protocol ist, siehe
[`2026-08-07-0805`](./2026-08-07-0805-fehlercodes-werden-abgeleitet-nicht-gepflegt.md)). Also muss
der Code die Aufgabe selbst uebernehmen.

Der Befund kam aus dem Tiefen-Struktur-Review von 0008, das im Response-Mapper eine tote,
dreifach gefuehrte Fehlertabelle fand. Beim Entfernen zeigte sich die Luecke dahinter.

## Die Entscheidung

**Jeder `match` ist vollstaendig.** Der letzte Zweig beantwortet einen echten Restfall oder wirft;
er endet nie offen.

Geworfen wird mit [`typing.assert_never`](https://docs.python.org/3/library/typing.html#typing.assert_never),
nicht mit einem selbstgebauten `RuntimeError`. Es ist der stdlib-Weg und traegt doppelt: zur
Laufzeit ein `AssertionError` mit dem unerwarteten Wert, und kaeme je ein Typpruefer dazu, meldete
er den nicht behandelten Fall schon beim Pruefen. Python hat keine `UnreachableException`;
`assert_never` ist das Gegenstueck.

## Die eine Unterscheidung: wem gehoert die Fallmenge?

`assert_never` behauptet "hier kommt nie etwas an". Das stimmt nur, wenn die Fallmenge **uns
gehoert und geschlossen ist** — eine Tagged Union dieses Repos, `Result`, ein Value Object.

Matcht der Code auf eine **offene Wertemenge aus fremder Hand**, ist der Restfall real und braucht
eine echte Antwort. Der Fall im Repo: `src/api/exception_handlers.py` matcht auf Pydantics
Fehlertyp-String. Ein neuer Pydantic-Fehlertyp ist ein Bibliotheks-Update, kein Programmierfehler —
mit `assert_never` quittierte eine harmlose Dependency-Aktualisierung jede unbekannte Eingabe mit
HTTP 500 statt mit einer uebersetzten 400.

Beide Formen erfuellen dieselbe Regel; sie unterscheiden sich nur darin, ob der Default erreichbar
ist. Die Pruefrage lautet nicht "kann das passieren?", sondern **"gehoert mir die Fallmenge?"**

## Warum kein Verzicht bei `Ok`/`Err`

Naheliegender Einwand: `Result` hat genau zwei Faelle, beide sind aufgezaehlt, der Default ist
tote Zeile. Trotzdem steht er da — aus demselben Grund, aus dem C# ihn auch bei einer versiegelten
Hierarchie mit zwei Ableitungen verlangt: **eine Regel, die eine Einzelfallabwaegung verlangt, wird
uneinheitlich angewandt.** "Ist diese Union wirklich geschlossen?" ist eine Frage, die jeder Leser
neu beantworten muesste. "Der letzte Zweig wirft" ist eine Frage, die ein Skript beantwortet.

## Umsetzung

13 `match`-Stellen in `src/` haben einen `case _: assert_never(<subjekt>)` bekommen. Drei davon
matchten auf einen Ausdruck statt auf einen Namen (`match await pipeline.run(...)`) — `assert_never`
braucht den gematchten Wert, also wird jetzt erst gebunden, dann gematcht.

Abgesichert wird die Regel nicht durch Erinnerung, sondern durch
`tests/test_match_exhaustiveness.py`: der Test liest `src/` per AST und laesst jeden `match`
durchfallen, dessen letzter Zweig weder wirft noch `assert_never` aufruft. Die offenen Wertemengen
stehen dort namentlich mit Begruendung; ein zweiter Test meldet einen Eintrag, der nicht mehr
gebraucht wird, damit eine veraltete Ausnahme nicht kuenftig eine echte Luecke zudeckt. Die
Mutationsprobe ist gelaufen: `assert_never` in `locale_tag` entfernt → Test rot mit genauer
Fundstelle, wieder eingesetzt → gruen.

Das folgt
[`exp_maschinelle-absicherung-statt-review-regel.md`](../reflections/exp_maschinelle-absicherung-statt-review-regel.md):
mechanisch entscheidbare Regeln gehoeren ins Gate, nicht in ein Review.

## Folgen

- `.rules/python/python-error-handling.md` hat den neuen Abschnitt "Jeder `match` ist
  vollstaendig". Die alte, falsche Begruendung ("`match` ohne Auffangzweig ist der Wachposten")
  ist dort korrigiert statt geloescht — sie war der Ausgangspunkt.
- Jeder kuenftige Slice erbt die Regel ueber das Gate, nicht ueber ein Review.
- Ticket 0048 (ruff `select = ["ALL"]`) beruehrt das nicht: ruff prueft keine
  match-Vollzaehligkeit, diese Luecke bliebe auch mit scharfem Linter offen.
