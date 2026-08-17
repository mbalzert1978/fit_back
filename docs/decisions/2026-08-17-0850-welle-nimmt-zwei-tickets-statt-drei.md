# Welle 2026-08-17 nimmt zwei Tickets statt drei — Feature-Slices warten auf die Referenzform

**Map:** [#40 — Die Tickets des Backend-Baus](https://github.com/mbalzert1978/fit_back/issues/40)

## Was entschieden wurde

Die Welle vom 2026-08-17 nimmt **#51** (M1: Restarbeit Stufe 4 — Pipeline-Abstraktion — plus
Contract-Test) und **#89** (M0: ungültigen Idempotency-Key gekürzt loggen). Die Concurrency-Kappung
von 3 wird bewusst **nicht ausgeschöpft**: die drei übrigen Tickets der Frontier — #71, #86, #90 —
bleiben liegen.

## Warum

Die Frontier zum Zeitpunkt der Wellenplanung: #51, #71, #86, #89, #90 offen und unblockiert
(11 von 50 Kindern geschlossen, 34 blockiert). Verifiziert über
`gh api --paginate repos/mbalzert1978/fit_back/issues/40/sub_issues`.

**#51 ist der Engpass, nicht das größte Ticket.** Von seiner Restarbeit war Stufe 4 offen: der
`register_user`-Slice hieß „Pipeline", war aber ein Wrapper mit einem `if` um den Handler — zwei
Fehlerkanäle, zwei Folds in dieselbe Response-Union. Der Slice ist zugleich die
**Referenzimplementierung der Slice-Form dieses Repos**:
`.claude/skills/review-against-rules/config.json` zeigt per `reference_implementation` darauf, und
die Kopfnotizen von `.rules/python/python-feature-slices.md` und `.rules/python/python-rule-pattern.md`
nennen ihn. Das Ticket sagt es selbst: „Ein falscher Schnitt hier wird zwangsläufig kopiert. Die
Stufe läuft deshalb **vor** dem nächsten Feature-Slice."

**#71 und #86 sind genau solche Feature-Slices.** Parallel gebaut entstünden sie gegen die alte
Form, die #51 gerade ersetzt — und wären in dem Moment, in dem #51 merged, Nachziehschuld in zwei
weiteren PRs. Das ist derselbe Fehler, den
[`exp_referenzimplementierung-schlaegt-prosa.md`](../reflections/exp_referenzimplementierung-schlaegt-prosa.md)
beschreibt, nur mit bekanntem Ablaufdatum. Die Parallelität hätte hier keinen Durchsatz gekauft,
sondern Rework.

**#90 fällt aus einem zweiten Grund heraus.** Es hat vier im Ticket ausdrücklich offene
Entscheidungen (Bezugsgröße des Limits, Ablage der Zähler, Antwortform, Reichweite), die vor der
Implementierung unter `docs/decisions/` zu klären sind — kein Auftrag, den ein Entwickler-Agent
blind ausführen kann. Zusätzlich träfe es dieselben Dateien wie #51
(`src/api/identity/register_user_router.py`, `src/main.py`).

**#89 bleibt übrig und passt.** Es ist mechanisch, klein, berührt nur
`src/middleware/idempotency.py` plus Tests, hat keine Slice-Form und ist damit von #51 paarweise
disjunkt.

## Was dadurch ausgeschlossen wird

- Die Kappung von 3 ist eine **Obergrenze, kein Soll**. Eine Welle mit zwei Tickets ist kein
  ungenutztes Budget, wenn das dritte Rework erzeugt hätte.
- #71, #86 und #90 sind **nicht** blockiert im Sinne von GitHub-Dependencies — sie bleiben offen
  und unblockiert. Wer die nächste Welle plant, nimmt sie **nach** dem Merge von #51 auf; erst dann
  steht die Form fest, an der sie sich ausrichten.
- Für #90 gilt zusätzlich: die vier offenen Entscheidungen werden **vor** der Implementierung
  getroffen und hier abgelegt, nicht vom implementierenden Agenten nebenbei.

## Nachtrag — warum die Regel-Nachführung ein eigener PR wurde

Ticket #51 verlangt einen Fehlertyp **je Use Case** (`RegisterUserError`) und eine Fehler-Union
**je Domain-Port** (`UserRegistryError`), während die Review-Checkliste in
`python-feature-slices.md` bis heute „context-eigen, nicht use-case-eigen" und „durchgehend
derselbe eine, flache Fehlertyp" fordert. Der implementierende Agent hatte die Regel-Datei
korrekterweise mitgezogen; dieser Commit wurde aus dem Feature-PR **herausgelöst** und liegt hier,
damit die Formfrage nicht nebenbei in einem Feature-PR entschieden wird.

Der Preis ist benannt und nicht wegzudiskutieren: solange nur der Feature-PR merged, beschreiben
Referenzimplementierung und Regel-Datei in genau diesen zwei Punkten verschiedene Formen — und
jeder Folge-Slice liest beide. **Beide PRs gehören zusammen gemergt**; wird dieser hier abgelehnt,
ist der Feature-PR nachzuziehen, nicht liegenzulassen.
