# Subagenten-Modell pro Agent statt globalem Riegel

**Datum:** 2026-08-13, 10:59
**Ticket:** [#21 Subagenten-Modell pro Agent statt global auf haiku](https://github.com/mbalzert1978/fit_back/issues/21)
(`wayfinder:task` der Map [#25](https://github.com/mbalzert1978/fit_back/issues/25))
**Status:** entschieden und umgesetzt; ein Nachweis steht bis zur nächsten Sitzung aus (siehe unten)

## Ausgangslage

`.claude/settings.json` setzte seit `aab056d` (2026-08-05, dem Commit, der `.claude/` überhaupt
angelegt hat) die Umgebungsvariable `CLAUDE_CODE_SUBAGENT_MODEL: haiku`. Gleichzeitig tragen
`senior-code-reviewer.md` und `fit-back-teamlead.md` beide `model: opus` im Frontmatter — die
beiden Agenten, die in der Ticket-Pipeline das QA- und das Security-Gate stellen und die Wellen
orchestrieren.

Das Ticket vermutete, die Variable überstimme das Frontmatter. Diese Prämisse wurde geprüft,
bevor sie beantwortet wurde (Regel aus [#22](https://github.com/mbalzert1978/fit_back/issues/22)).

## Gemessen, nicht geglaubt

Claude Code protokolliert je Subagenten-Lauf zwei Dinge getrennt: `.meta.json` hält fest, *was
angefordert* wurde, das Transkript daneben, *worauf es tatsächlich lief*. Ausgewertet wurden alle
63 Subagenten-Läufe dieses Projekts unter
`~/.claude/projects/c--temp-apps-fit-back/*/subagents/`, verteilt über den 5., 6. und 13. August:

| Agent | Frontmatter | `model` am Aufrufort | tatsächlich gelaufen | Läufe |
|---|---|---|---|---|
| `senior-code-reviewer` | `model: opus` | — | `claude-haiku-4-5` | 15 |
| `senior-code-reviewer` | `model: opus` | `sonnet` | `claude-haiku-4-5` | 1 |
| `fit-back-teamlead` | `model: opus` | — | `claude-haiku-4-5` | 12 |
| `general-purpose` | — | `sonnet` | `claude-haiku-4-5` | 11 |
| `general-purpose` / `claude` / `Explore` | — | — | `claude-haiku-4-5` | 24 |

**Kein einziger Lauf auf einem anderen Modell.** Der Befund geht über die Behauptung des Tickets
hinaus: die Variable überstimmt nicht nur das Frontmatter, sondern auch den **expliziten
`model`-Parameter am Aufrufort** — elf Aufrufe haben ausdrücklich `sonnet` angefordert und Haiku
bekommen.

Sie ist damit **kein Default, sondern ein Riegel**: solange sie steht, gibt es keinen Weg, einen
Subagenten dieses Repos auf ein anderes Modell zu bringen. `model: opus` in beiden Agenten-Dateien
war toter Text.

Weil die Variable seit dem allerersten `.claude/`-Commit steht, gibt es keinen Zeitraum ohne sie,
gegen den sich vergleichen ließe. Der Riegel ist über den vollen Zeitraum belegt, seine Abwesenheit
nicht — daher der ausstehende Nachweis unten.

## Entscheidung

1. **`CLAUDE_CODE_SUBAGENT_MODEL` ersatzlos aus `.claude/settings.json` entfernt.** Kein Ersatz für
   die eingebauten Agenten (`general-purpose`, `Explore`, `claude`, `Plan`), die kein Frontmatter
   in unserer Hand haben und nun das Hauptmodell erben. Sie mit eigenen Dateien zu überschatten
   hieße, drei Dateien gegen ein Problem zu bauen, das noch niemand hatte; die teuren Läufe sind
   die der Pipeline, und deren Agenten deklarieren ihr Modell selbst. Soll ein
   `general-purpose`-Lauf billig bleiben, sagt das der Aufrufort — und *das* greift nach dem Ausbau
   wieder.
2. **`semble-search.md` bekommt ein explizites `model: haiku`.** Der Agent trug bisher keins und
   hätte nun Opus geerbt, für das Aufrufen einer CLI und das Referieren ihrer JSON-Ausgabe. Damit
   nennt **jede** projektlokale Agenten-Datei ihr Modell selbst; implizit bleibt nichts.

`MAX_THINKING_TOKENS: 10000` steht aus demselben Commit in derselben `env`-Klammer und ist von
derselben Bauart — ein globaler Riegel auf etwas, das die Aufrufstelle sonst selbst bestimmt. Es
wurde hier **nicht** mitentschieden, sondern als Nebel auf der Map notiert: für diese Frage gibt es
noch keine einzige Messung.

## Der eigentliche Fund: `env` friert beim Sitzungsstart ein

Die Gegenprobe nach dem Ausbau ergab, dass die Variable **weiterhin** in der Umgebung der
Tool-Shell steht, unverändert auf `haiku`, obwohl die Datei sie nicht mehr enthält.

Damit ist die Notiz auf der Map — „Änderungen an `.claude/settings.json` wirken ohne Neustart der
Sitzung", gemessen im Worktree-Wächter-Durchgang
([#20](https://github.com/mbalzert1978/fit_back/issues/20)) — **zu breit formuliert**. Sie gilt für
**Hook-Registrierungen**, die vor jedem Aufruf neu gelesen werden. Sie gilt **nicht** für den
`env`-Block: der wird beim Sitzungsstart in die Prozessumgebung übernommen und danach nicht mehr
angefasst. Der Ausbau wirkt erst in der **nächsten** Sitzung.

Das ist dieselbe Regelfamilie ein weiteres Mal, jetzt auf einen bereits gemessenen Fakt angewandt:
[#22](https://github.com/mbalzert1978/fit_back/issues/22) prüft die **Ausgangslage**,
[#20](https://github.com/mbalzert1978/fit_back/issues/20) die **mitgelieferte Lösung**,
[#30](https://github.com/mbalzert1978/fit_back/issues/30) den **Ausfallmodus**,
[#29](https://github.com/mbalzert1978/fit_back/issues/29) den **Geltungsbereich eines Kommandos** —
und hier den **Geltungsbereich einer früheren Messung**: „Settings wirken sofort" wurde an Hooks
gemessen und deckt den `env`-Block nicht mit ab.

Praktisch heißt das: ein Nachweis-Lauf **in dieser Sitzung** hätte weiter Haiku gezeigt und wäre als
„Ausbau wirkungslos" fehlgedeutet worden.

## Ausstehender Nachweis

Das Abnahmekriterium des Tickets verlangt „ein Gate-Lauf nachweislich auf dem im Frontmatter
genannten Modell". Der erste Teil ist erfüllt (die Variable steht nirgends mehr), der zweite kann
erst nach einem Sitzungsneustart gemessen werden. Die Prüfung ist ein Einzeiler — nach dem nächsten
Start irgendeines Subagenten:

```bash
cd ~/.claude/projects/c--temp-apps-fit-back
for m in */subagents/*.meta.json; do b="${m%.meta.json}"; \
  echo "$(jq -r .agentType "$m") -> $(jq -r 'select(.type=="assistant") | .message.model' "$b.jsonl" | sort -u)"; \
done | tail -5
```

Erwartet: `senior-code-reviewer` und `fit-back-teamlead` auf `claude-opus-…`, `semble-search` auf
`claude-haiku-…`.

## Nebenbefund: 28 Gate-Läufe auf Haiku

Sechzehn `senior-code-reviewer`- und zwölf `fit-back-teamlead`-Läufe seit dem 5. August liefen auf
einem Modell, das für diese Rolle nie gewählt wurde — jedes QA- und Security-Gate der Pipeline und
jede Wellen-Orchestrierung dieses Zeitraums.

Ein pauschales Nachreview der gemergten PRs wird **nicht** angesetzt: die Gates haben ja gearbeitet,
und der Aufwand ginge ins Blaue. Der Befund steht hier und in den Notes der Map, damit ein späteres
Ticket, das sich auf ein grünes Gate von vor dem 2026-08-13 beruft, weiß, worauf es sich beruft.

Es ist zudem derselbe Ausfallmodus, den diese Map schon zweimal notiert hat: **es ist nie etwas
fehlgeschlagen.** 63 Subagenten-Läufe endeten sauber, auf einem Modell, das niemand für sie
angefordert hatte — die Fehlbesetzung war nur an einer Stelle sichtbar, an der niemand nachsah.
