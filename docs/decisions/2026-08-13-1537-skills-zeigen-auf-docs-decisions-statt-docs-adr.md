# Skills zeigen auf `docs/decisions/` statt `docs/adr/` — über `config.json`, nicht über den Skill-Text

**Datum:** 2026-08-13, 15:37
**Ticket:** [#35 — docs-code-consistency und verify-issue-breakdown auf CONTEXT.md und docs/decisions/ umhaengen](https://github.com/mbalzert1978/fit_back/issues/35)
**Map:** [#25 — Hook-Portfolio und semble-Anbindung des Claude-Setups](https://github.com/mbalzert1978/fit_back/issues/25)

## Die Prämisse des Tickets hielt nur zur Hälfte

Das Ticket — und mit ihm [#27](https://github.com/mbalzert1978/fit_back/issues/27) — nahm an,
**beide** Skills nennten `CONTEXT.md` und `docs/adr/`. Gemessen stimmt das nur für
`docs-code-consistency`. `verify-issue-breakdown` nennt keinen der beiden Pfade: es hat ein
optionales Argument `glossary_path`, sucht sonst selbst und ließ seine Vokabular-Teilprüfung bei
Nichtfund still ausfallen. Das war schon im Nachtrag aus
[#34](https://github.com/mbalzert1978/fit_back/issues/34) am Ticket vermerkt und hat sich bestätigt.

Damit zerfällt die Arbeit in zwei verschiedene Aufgaben statt einer.

## Was entschieden wurde

**1. `docs/adr/` verschwindet aus `docs-code-consistency`, und der Ersatzpfad steht in
`config.json`, nicht im Skill-Text.**

Die Rolle, die `docs/adr/` anderswo spielt, spielt hier `docs/decisions/`. Beide Skills sind
repo-übergreifende Infrastruktur — ein hart verdrahteter Repo-Pfad im Skill-Text wäre in jedem
anderen Repo falsch. Der vorgesehene Ort für repo-spezifische Pfade ist `config.json`; dort steht
jetzt `decision_docs_dir: "docs/decisions"`, und der Skill-Text nennt nur noch den Schlüssel.
Das ist dieselbe Bauart, die `architecture-adr-check` mit seinem `adr_dir` schon hat.

Die übrigen `ADR`-Nennungen im Fließtext (Beschreibung, `arguments`, Prüfumfang, Beispieltabelle,
Skript-Hilfetext) sind auf „decision docs" umformuliert. Der Beispiel-Tabelleneintrag nennt
`<decision_docs_dir>/…` statt eines echten Pfades — ein Beispiel soll nichts über ein bestimmtes
Repo behaupten.

**2. Ein fehlendes Artefakt meldet sich, statt still zu bleiben — in beiden Skills.**

Die Lektion aus [#22](https://github.com/mbalzert1978/fit_back/issues/22)/[#30](https://github.com/mbalzert1978/fit_back/issues/30)
und [#31](https://github.com/mbalzert1978/fit_back/issues/31) gilt hier direkt: *ein Werkzeug, das
still ausfällt, sieht aus wie ein sauberes Ergebnis.* Beide Skills hatten genau diese Lücke:

- `docs-code-consistency` hätte einen nicht existierenden Entscheidungs-Ordner einfach nicht
  gelesen und trotzdem `PASS` melden können. Jetzt endet der Lauf mit `Verdict: CONFIG ERROR` und
  nennt den Pfad, wenn `decision_docs_dir` fehlt oder ins Leere zeigt — dieselbe Regel, die
  `lint-and-format-check`, `review-against-rules` und `structure-placement-check` schon befolgen.
- `verify-issue-breakdown` bekommt kein `CONFIG ERROR` (die Vokabular-Prüfung ist ausdrücklich eine
  weiche Teilprüfung und darf Kriterium 6 nicht allein zum Scheitern bringen), aber der Bericht
  muss sagen, woran sie gemessen hat: das Template trägt jetzt eine Zeile
  `Vocabulary source: {{VOCABULARY_SOURCE}}`, die entweder die gelesene Quelle nennt oder
  `not found — vocabulary sub-check skipped` samt Suchorten. Leer bleiben darf sie nie.

## Was dadurch ausgeschlossen ist

- **Kein Umhängen bei `verify-issue-breakdown`.** Es gab keinen Pfad zu korrigieren; ihm einen
  festzuschreiben — auch über `config.json` — hätte eine Selbstsuche ersetzt, die funktioniert,
  seit `CONTEXT.md` seit Commit `ceea203` im Repo-Root liegt. Der Fundort wird nicht benannt.
- **Keine Bereinigung der übrigen Skills.** `grill-with-docs` und `improve-codebase-architecture`
  nennen `docs/adr/` weiterhin; `architecture-adr-check` trägt es als Default in seiner
  `config.json`. Das lag außerhalb dieses Tickets und ist noch nicht entschieden.
