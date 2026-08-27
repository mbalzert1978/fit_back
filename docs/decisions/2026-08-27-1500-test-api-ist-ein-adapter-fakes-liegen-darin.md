# Die Test-API ist ein Adapter — und die Fakes liegen in ihr

## Was entschieden wurde

Innerhalb eines Use Case gilt ab sofort:

```
application/<use_case>/
  adapters/
    test_api/
      fakes/
```

Die Test-API liegt **unter `adapters/`**. Die In-Memory-Fakes liegen **in der Test-API**, nicht
daneben.

Ersetzt die bisherige Form, in der `test_api/` und `fakes/` Geschwister direkt unter
`application/<use_case>/` waren.

## Warum

**Die Test-API ist selbst ein Adapter.** Sie bedient dieselbe Naht wie die Produktions-Adapter —
nur mit Fakes dahinter statt echter Infrastruktur. Sie neben `adapters/` zu stellen behauptet, sie
sei eine eigene Kategorie. Ist sie nicht. Sie ist derselbe Anti-Corruption-Layer, anders verdrahtet.

**Die Fakes haben ausserhalb der Test-API keinen Abnehmer.** Ein `fakes/` als Geschwister der
Test-API suggeriert eine Benutzbarkeit, die es nicht gibt: kein Spec darf die Fakes direkt
anfassen — das verbietet `slice-shape-check` über das Import-Fragment `.fakes`. Ein Ordner, den nur
genau ein Nachbar benutzen darf, gehört in diesen Nachbarn.

Beides ändert nichts an der bisherigen Aussage, dass die Test-API **ausgelieferter Bestandteil des
Slice** ist und nicht zum Testprojekt gehört. Die Begründung dafür steht unverändert in
[`2026-08-06-0751-slice-form-test-api-baureihenfolge.md`](2026-08-06-0751-slice-form-test-api-baureihenfolge.md).

## Was mit verschoben wurde

Die Modul-Dateien der Fakes tragen im Ordner `fakes/` keine Präfixe mehr — `in_memory_`,
`passthrough_`, `deterministic_` waren im Kontext des Ordners doppelt. Die **Klassennamen** bleiben
unverändert (`InMemoryUserStore`, `PassthroughIdnLabels`, `DeterministicPasswordHasher`). Anlass
war ein harter Zwang: die tiefere Schachtelung sprengte sonst das Zeilenlimit von 100 Zeichen in
den Importzeilen.

## Nicht entschieden

Die Domänenschicht bleibt, wo sie ist. **Ein Bounded Context = eine `domain/`-Schicht**, geteilt
von allen Use Cases des Contexts — so wie es in
[`.rules/python/python-feature-slices.md`](../../.rules/python/python-feature-slices.md) bereits
steht und wie DDD und CQRS es üblicherweise handhaben: der Slice schneidet die
Application-Schicht, nicht die Domäne. Braucht ein Slice wirklich ein eigenes Domänenmodell, ist er
in Wahrheit ein eigener Bounded Context — dann wird dort getrennt, nicht beim Slice.

## Was nachgezogen wurde

- [`.rules/python/python-feature-slices.md`](../../.rules/python/python-feature-slices.md) —
  Slice-Baum, Abschnitt „Die Test-API ist Teil des Slice", Checkliste
- [`docs/architecture.md`](../architecture.md) — Context-Baum
- [`docs/milestones/00-overview.md`](../milestones/00-overview.md) — Stufe 1, Mehrfach-Use-Case-Hinweis
- `.claude/skills/slice-shape-check/` — `config.json` (`required_dirs`), `SKILL.md`, Skript-Docstring
- `.claude/skills/review-against-rules/config.json` — Beschreibung der Referenzimplementierung
