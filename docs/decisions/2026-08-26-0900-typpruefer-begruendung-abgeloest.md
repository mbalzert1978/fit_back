# Die Begruendung „dieses Repo hat keinen Typpruefer" ist abgeloest

**Datum:** 2026-08-26, 09:00
**Status:** entschieden, umgesetzt
**Loest ab:** die Typpruefer-Begruendung in
[`2026-08-07-1120-jeder-match-endet-mit-assert-never.md`](./2026-08-07-1120-jeder-match-endet-mit-assert-never.md)
— nicht deren Regel.

## Der Anlass

Beim Eindampfen der Docstrings fiel auf, dass mehrere Stellen im Repo eine Tatsache behaupten,
die seit Issue #97 nicht mehr gilt: dieses Repo faehre bewusst ohne Typpruefer. `ty` (Astral)
ist seit dem 2026-08-25 konfiguriert, laeuft als Gate in `./make.ps1 ci` und prueft `src/` seit
dem 2026-08-26 vollstaendig ohne Baseline
([`2026-08-25-1500-typechecker-ty.md`](./2026-08-25-1500-typechecker-ty.md)).

Betroffen waren fuenf Stellen im Code und zwei in `.rules/`. Sie stammen alle aus derselben
Zeit und aus derselben Begruendungskette: weil kein Typpruefer da sei, muesse der Code die
Vollzaehligkeit selbst absichern — per `assert_never`, per Laufzeitpruefung beim Start, per
Test, der die Fallmengen zaehlt.

## Was entschieden wird

**Die Begruendung ist abgeloest, die Regeln bleiben.**

Beides auseinanderzuhalten ist der Kern dieser Entscheidung. Die Regeln aus
`2026-08-07-1120` — jeder `match` ist vollstaendig, der letzte Zweig ruft `assert_never`,
ohne Abwaegung an der Schreibstelle — gelten unveraendert weiter. Was faellt, ist nur der
Halbsatz, der sie mit einer fehlenden Werkzeugkette begruendet hat.

Denn die Regel steht heute auf einem besseren Fundament, nicht auf einem schlechteren:

- **`ty` loest die `Never`-Zusage ein.** `assert_never` war 2026-08-07 reiner Laufzeitschutz;
  der zweite Nutzen stand dort ausdruecklich im Konjunktiv („kaeme je ein Typpruefer dazu").
  Er ist jetzt eingetreten. Ein nicht behandelter Fall einer geschlossenen Union meldet sich
  beim Pruefen statt im Betrieb.
- **Die Laufzeit-Absicherungen bleiben trotzdem noetig.** `ty` traegt nur, wo die Fallmenge
  geschlossen ist. Ueber offene Mengen — Pydantics Fehlertyp-Strings, i18n-Schluessel aus
  Ressourcendateien, Event-Typen aus einer Outbox-Zeile — sagt kein Typpruefer etwas zu. Die
  Startpruefung in `src/api/i18n_startup_check.py` und die messenden Tests
  (`tests/test_match_exhaustiveness.py`,
  `tests/contexts/identity/test_register_user_error_channel.py`) verlieren dadurch nichts.
  Sie sind kein Ersatz mehr fuer ein fehlendes Werkzeug, sondern die Absicherung dort, wo
  das vorhandene nichts sagen kann.

## Was daraus im Code folgt

Die Absicherungen begruenden sich ab jetzt aus dem, was sie messen — nicht aus dem, was fehlt.
Konkret entfernt wurden die Verweise auf einen fehlenden Typpruefer in:

- `src/api/i18n_startup_check.py`
- `src/contexts/identity/application/register_user/errors.py`
- `tests/test_match_exhaustiveness.py`
- `tests/test_i18n_drift.py`
- `tests/contexts/identity/test_register_user_error_channel.py`

In `.rules/python/python-error-handling.md` sind beide Stellen korrigiert statt geloescht:
der Abschnitt „Jeder `match` ist vollstaendig" nennt jetzt `ty` als das Werkzeug, das die
Zusage einloest, und dazu dessen Grenze.

## Die eine neue Regel

Dazugekommen ist ein Punkt, den es vor `ty` nicht geben konnte:

**Gematcht wird in zwei Stufen — erst der Ausgang (`Ok` / `Err`), dann der Fehlerwert selbst.**

Steht der Fehlerfall verschachtelt im Muster (`case Err(error=EmailIsEmpty())`), traegt `ty`
die Einengung nicht ins Typargument von `Err` hinein. Der Restfall bleibt fuer den Pruefer
`Err[EmailError]` statt `Never`, und `assert_never` faellt auf reinen Laufzeitschutz zurueck —
also genau auf den Stand von 2026-08-07. Gemessen an `register_user_rules.py` und
`register_user_response_mapper.py`, wo beide Formen durchprobiert wurden.

Das ist keine Stilfrage. Es entscheidet, ob die Zusage statisch gilt oder nur behauptet ist.

## Was ausdruecklich nicht faellt

- **Die Ausnahme in `_fault_of`** (`src/api/exception_handlers.py`) bleibt. Dort steht ein
  Wurf statt `assert_never`, weil `error["type"]` ein `str` ist und `str` keine geschlossene
  Fallmenge hat. Die Regel gilt unveraendert; die Stelle markiert sich selbst als Ausnahme,
  wie es
  [`exp_standard-ausnahme-am-ort-markieren.md`](../reflections/exp_standard-ausnahme-am-ort-markieren.md)
  vorschreibt.
- **`2026-08-07-1120` als Ganzes.** Das Dokument haelt fest, was am 2026-08-07 galt und warum
  so entschieden wurde. Es wird nicht umgeschrieben. Wer es liest, findet ueber den Status-Block
  dieses Dokument.
- **`CodedError` als `@runtime_checkable` Protocol**
  ([`2026-08-07-0805`](./2026-08-07-0805-fehlercodes-werden-abgeleitet-nicht-gepflegt.md)).
  Die Codes werden aus den Unions abgeleitet und zur Startzeit gegen die Ressourcendateien
  geprueft; das ist eine Frage von Daten, nicht von Typen.

## Folgen

- Kein Text in `src/`, `tests/` oder `.rules/` behauptet mehr, dieses Repo habe keinen
  Typpruefer.
- `docs/decisions/2026-08-07-1120-jeder-match-endet-mit-assert-never.md` traegt einen
  Status-Verweis hierher.
- Wer kuenftig eine Laufzeitpruefung mit „wir haben ja keinen Typpruefer" begruenden will,
  begruendet sie stattdessen mit der offenen Fallmenge, um die es tatsaechlich geht.
