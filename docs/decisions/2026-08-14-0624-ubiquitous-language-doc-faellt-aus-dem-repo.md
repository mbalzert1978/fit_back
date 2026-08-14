# `ubiquitous-language-doc` fällt aus dem Repo — der Generator hat hier keinen Anlass

**Datum:** 2026-08-14, 06:24
**Ticket:** [#37 — ubiquitous-language-doc überschreibt CONTEXT.md — bleibt das Skill?](https://github.com/mbalzert1978/fit_back/issues/37)
**Map:** [#25 — Hook-Portfolio und semble-Anbindung des Claude-Setups](https://github.com/mbalzert1978/fit_back/issues/25)

## Die Prämisse des Tickets hielt nicht

Das Ticket fürchtete, ein Lauf des Skills **überschreibe** die seit [#34] handverlesene
`CONTEXT.md`, „ohne dass jemand es merkt". Das steht so nicht in seinem Text. Schritt 1 der
`SKILL.md` kennt einen Refresh-Modus:

> **Exists** → **refresh mode**: read it first and *reconcile*, don't overwrite. […] preserve
> human-authored prose and any `_Avoid_` lines that still hold.

Ein Lauf hätte die Datei also ergänzt, nicht ersetzt. Die im Ticket vorgeschlagene Nachbesserung
„auf ergänzen statt erzeugen umschreiben" wäre auf eine Eigenschaft hinausgelaufen, die das Skill
schon hat.

## Der echte Konflikt: die Iron Rule gegen das Bauprinzip der Datei

Das Skill trägt eine **Iron Rule**, und die ist mit `CONTEXT.md` unvereinbar:

> **Every term, definition, invariant, and *Avoid* entry MUST come from the actual code** […]
> A glossary you could have written without opening the code is a failed run.

`CONTEXT.md` sagt in ihrer eigenen dritten Zeile das Gegenteil:

> **Jeder Eintrag geht auf einen im Repo dokumentierten Streitfall zurück.** Ein Begriff kommt
> hinzu, wenn ein Ticket ihn schärft — nicht auf Vorrat.

Die beiden Regeln haben unterschiedliche **Aufnahmekriterien**: der Code gegen den Streitfall. Über
124 Python-Dateien im Repo hätte ein Refresh zentrale Typen als Begriffe eingetragen, über die nie
jemand gestritten hat — genau den Vorrat, den [#27] ausgeschlossen hat. Das ist kein Bug im Skill;
es ist seine Bestimmung. Sie passt hier nur nicht.

Ein Riegel in der `description` hätte diesen Widerspruch nicht aufgelöst, sondern nur seine
Auslösung unwahrscheinlicher gemacht — und dafür ein Skill im Bestand gehalten, dessen einziger
Zweck es dann wäre, nicht zu laufen.

## Der dritte Befund: Schritt 4 war schon tot

Schritt 4 („wire it into `CLAUDE.md`") schreibt seinen Zeiger unter die Überschrift aus
`config.json`: `## Architecture`. Die gibt es in `CLAUDE.md` seit [#33] nicht mehr, und den Link
auf `CONTEXT.md` setzt seit [#34] niemand mehr neu. Von den sechs Prozessschritten des Skills
waren damit zwei gegenstandslos, bevor irgendwer sie ausgeführt hätte.

## Entscheidung

Die Repo-Kopie `.claude/skills/ubiquitous-language-doc/` wird **gelöscht**. Der Bestand fällt damit
demselben Kriterium zum Opfer wie die neun Hooks aus [#18]/[#28]: kein Anlass im Repo.

Nachgezogen wurden die zwei Index-Stellen — der Baum und die Bucket-Liste in
`.claude/skills/CLAUDE.md`, sowie der Eintrag in `sync-skill-index/config.json`, aus dem beide
generiert werden. Danach null Restverweise im Repo.

## Was das Löschen **nicht** tut — der Fund aus der Ausführung

Der Skill blieb nach dem `git rm` verfügbar. Er hat einen **zweiten, globalen Zwilling**:

- `~/.agents/skills/ubiquitous-language-doc/` — die zentrale Quelle,
- `~/.claude/skills/ubiquitous-language-doc` → Symlink darauf, greift in **jedem** Repo,
- `.claude/skills/ubiquitous-language-doc/` — die hiesige Kopie, jetzt weg.

Die beiden Fassungen waren **auseinandergelaufen**: `diff -rq` meldet für alle drei Dateien
(`SKILL.md`, `config.json`, `assets/`) Unterschiede. Es war kein Klon, sondern eine zweite Version.

Der globale bleibt **absichtlich stehen**. Er ist keine Konfiguration dieses Repos und liegt damit
außerhalb der Domäne dieser Map; andere Repos tragen das Bauprinzip aus [#27] nicht und dürfen
ihren Generator behalten. Wer ihn hier trotzdem aufruft, liest als erstes die dritte Zeile von
`CONTEXT.md` — der Riegel steht in der Datei selbst, nicht in einer Skill-Beschreibung, und ist
damit an der Stelle, an der er ohnehin gelesen werden muss.

## Regel für diese Map

**Ein Löschen wirkt nur so weit wie das Verzeichnis, in dem es stattfindet.** Diese Map hat neun
Hooks gelöscht und Dateien umgezogen; alle lagen im Repo, und „weg" hieß dort weg. Ein Skill kann
dreifach vorliegen — Repo-Kopie, zentrale Quelle, globaler Symlink — und ein `git rm` sieht davon
genau eine. Die Frage ist deshalb nicht nur „soll das weg?", sondern **„wie viele Fassungen gibt es,
und welche davon erreicht dieses Repo noch?"** — hier belegt durch die Skill-Liste, die den Namen
unmittelbar nach dem Löschen erneut anbot.

Die elfte Stufe derselben Familie: [#22] prüft die **Ausgangslage**, [#20] die **mitgelieferte
Lösung**, [#30] den **Ausfallmodus**, [#29] den **Geltungsbereich eines Kommandos**, [#21] den
**einer eigenen früheren Notiz**, [#27] die **Anzahl der Stellen**, [#28] die **Richtung einer
Kante**, [#26] die **Haltbarkeit eines Berechtigungsbefunds**, [#32] **benannte Fehlstelle gegen
Bestandsaufnahme**, [#33] die **Rückrichtung** — und hier die **Reichweite**: wo eine Sache sonst
noch liegt.

[#18]: https://github.com/mbalzert1978/fit_back/issues/18
[#20]: https://github.com/mbalzert1978/fit_back/issues/20
[#21]: https://github.com/mbalzert1978/fit_back/issues/21
[#22]: https://github.com/mbalzert1978/fit_back/issues/22
[#26]: https://github.com/mbalzert1978/fit_back/issues/26
[#27]: https://github.com/mbalzert1978/fit_back/issues/27
[#28]: https://github.com/mbalzert1978/fit_back/issues/28
[#29]: https://github.com/mbalzert1978/fit_back/issues/29
[#30]: https://github.com/mbalzert1978/fit_back/issues/30
[#32]: https://github.com/mbalzert1978/fit_back/issues/32
[#33]: https://github.com/mbalzert1978/fit_back/issues/33
[#34]: https://github.com/mbalzert1978/fit_back/issues/34
