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

## Ohne Ausnahme — auch bei fremden Fallmengen

Der erste Entwurf dieser Entscheidung hatte eine Ausnahme vorgesehen: matcht der Code auf eine
**offene Wertemenge aus fremder Hand** — Pydantics Fehlertyp-Strings in
`src/api/exception_handlers.py` —, sei der Restfall real und brauche eine echte Antwort statt
`assert_never`. Begruendung: ein neuer Pydantic-Fehlertyp ist ein Bibliotheks-Update, kein
Programmierfehler, und duerfe den Aufrufer nicht mit HTTP 500 treffen.

**Diese Ausnahme ist verworfen.** Eine Aenderung, die wir nicht adressiert haben, ist ebenso ein
Bruch — ob sie aus unserem Code kommt oder aus einer Abhaengigkeit, aendert daran nichts. Sie still
auf einen Auffangzweig abzubilden heisst, dem Aufrufer eine falsche Begruendung zu nennen.

Der Beleg lag im Code: der Auffangzweig bildete `model_attributes_type` (der Body ist ein Array
statt eines Objekts) auf `field-type-error` ab. Der Aufrufer las **"Das Feld '' muss ein Text
sein"** — mit leerem Feldnamen, weil es gar kein Feld gibt. Der Zweig hat den Fehler nicht
abgefedert, er hat ihn verdeckt. Er ist jetzt ein eigener Fall (`BodyNotAnObject`) mit eigenem Code
und eigenem Text.

## Der Einwand, der dabei richtig bleibt

Ein `assert_never` an dieser Stelle wirkt erst **zur Anfragezeit** — der Bruch traefe einen Nutzer
in Produktion mit HTTP 500, nicht das Deployment. Das ist zu spaet. Deshalb wird die Annahme
zweimal frueher geprueft:

- **Beim Start** (`src/api/pydantic_contract_check.py`): existiert jeder behandelte Fehlertyp im
  installierten Pydantic ueberhaupt noch? Ein umbenannter oder entfernter Typ stoppt den Start.
- **In der CI** (`tests/api/test_pydantic_error_contract.py`): erzeugt der Endpunkt noch genau die
  Typen, die der Handler abbildet — in beide Richtungen, damit weder ein unbehandelter Typ noch ein
  toter Zweig stehen bleibt.

Der Start prueft die **Existenz**, die CI das **Verhalten**. `assert_never` ist die letzte Instanz
dahinter, nicht die erste.

## Was das Messen gelehrt hat

Die Menge der erreichbaren Fehlertypen wurde dreimal korrigiert, jedes Mal weil gemessen statt
angenommen wurde:

1. Erste Messung gegen `RegisterUserBody` direkt: fuenf Typen.
2. Der Testlauf fand `value_error` — den erzeugt jedes Modell mit einem `field_validator`, und der
   Handler haengt app-weit, nicht an einem Modell.
3. Der HTTP-Test fand `model_attributes_type`, wo die Modellmessung `model_type` geliefert hatte:
   FastAPI legt eine eigene Validierungsschicht um den Body, und die meldet einen anderen Typ als
   `RegisterUserBody.model_validate([])`. **Wer nur das Modell faehrt, misst einen Vertrag, den der
   Handler nie sieht.** Der Vertragstest laeuft deshalb durch den echten Endpunkt.

Jede dieser drei Korrekturen kam von einem roten Test, keine vom Nachdenken.

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
durchfallen, dessen letzter Zweig weder wirft noch `assert_never` aufruft — **ohne Ausnahmeliste**.
Die Mutationsprobe ist gelaufen: `assert_never` in `locale_tag` entfernt → Test rot mit genauer
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
