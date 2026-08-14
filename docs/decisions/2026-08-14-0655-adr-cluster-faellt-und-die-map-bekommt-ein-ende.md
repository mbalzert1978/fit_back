# Das ADR-Skill-Cluster fällt, und die Map bekommt ein Ende

**Datum:** 2026-08-14, 06:55
**Tickets:** [#38](https://github.com/mbalzert1978/fit_back/issues/38), [#39](https://github.com/mbalzert1978/fit_back/issues/39)
**Map:** [#25 — Hook-Portfolio und semble-Anbindung des Claude-Setups](https://github.com/mbalzert1978/fit_back/issues/25)

## Der Anlass war eine Beschwerde, kein Ticket

Markus hat drei Dinge auf einmal beanstandet: dass die betroffenen Skills veraltet seien, dass
[#16](https://github.com/mbalzert1978/fit_back/issues/16),
[#19](https://github.com/mbalzert1978/fit_back/issues/19) und
[#24](https://github.com/mbalzert1978/fit_back/issues/24) seit Tagen unbearbeitet liegen, und
dass für die Minimierung von `CLAUDE.md` drei Tage draufgegangen sind. Alle drei trafen zu.

## Was entschieden wurde

**1. `grill-with-docs`, `improve-codebase-architecture` und `deepen-module` fallen aus dem Repo.**

Gemessen ruft in diesem Repo **nichts** die drei auf — außer ihnen selbst und dem Skill-Index.
Sie sind ein geschlossener Dreier-Kreis: `deepen-module` holt sein Vokabular aus
`improve-codebase-architecture/LANGUAGE.md` und übergibt sein Interview an `grill-with-docs`.
Dazu kam ein aktiver Schaden: `grill-with-docs` legt laut `ADR-FORMAT.md` das Verzeichnis
`docs/adr/` **lazily an** und schreibt Entscheidungen mit fortlaufender Nummerierung hinein —
gegen `CLAUDE.md` und gegen die Benennung in `docs/decisions/README.md`.

Gleiche Behandlung wie [#37](https://github.com/mbalzert1978/fit_back/issues/37) bei
`ubiquitous-language-doc`: Repo-Kopie raus, globale Zwillinge unter `~/.agents/skills/` bleiben
stehen. `sync-skill-index/config.json` und `.claude/skills/CLAUDE.md` nachgezogen, null
Restverweise. **Der Dritte war nicht vorgesehen** — die Entscheidung lautete zunächst auf zwei;
`deepen-module` kam dazu, weil es nach dem Löschen der beiden anderen sechs tote relative Links
und keine Funktion mehr gehabt hätte.

**2. `architecture-adr-check` liest jetzt `docs/decisions/` — und hat vorher stumm durchgewunken.**

`adr_dir` stand auf `docs/adr`, ein Verzeichnis, das es hier nicht gibt. `list_adrs` macht
`adr_dir.glob("*.md")`, und `glob` auf ein fehlendes Verzeichnis liefert leer statt zu scheitern.
Der Skill meldete „keine ADRs betroffen" und gab **PASS**. Er läuft als Gate im
[`fit-back-teamlead`](../../.claude/agents/fit-back-teamlead.md)-Agenten, also in der
Ticket-Pipeline — diese Hälfte seiner Arbeit hat er seit dem Wegfall von `docs/adr/` nie getan.
Nach dem Wertwechsel findet er 41 Einträge statt 0.

Hingenommen: alle 41 tragen die ID `2026` (`re.match(r"(\d+)-")` greift das Datumspräfix), und
`docs/decisions/README.md` läuft als vermeintliche Entscheidung mit. Der Dateipfad steht daneben.

**Bewusst nicht gemacht: fail-loud.** [Das Decision-Doc vom 2026-08-13](2026-08-13-1537-skills-zeigen-auf-docs-decisions-statt-docs-adr.md)
hat für das Schwester-Skill `docs-code-consistency` genau das Gegenteil entschieden — `CONFIG ERROR`,
wenn der Pfad ins Leere zeigt. `architecture-adr-check` bleibt damit als einziges Gate-Skill ohne
diesen Riegel. Die Abweichung ist bekannt und nicht versehentlich.

**3. #16, #19 und #24 gehören in die Map — die Ausgrenzung war ein Fehler mit praktischer Wirkung.**

Sie standen im `Out of scope`-Abschnitt mit der Begründung, sie folgten aus keiner Entscheidung
der Map. Das hält nicht: alle drei fassen `.claude/` an, also genau die Domäne der Map, und deren
erste Note trägt die Ausführung ohnehin mit. Der Schaden war nicht kosmetisch: **die
Frontier-Abfrage sieht nur Kinder der Map.** Drei offene Tickets blieben deshalb tagelang
unsichtbar, während frischer Nebel zu neuen Tickets verarbeitet wurde — es sah nach Fortschritt
aus, während die echte offene Arbeit danebenlag.

**4. Der Nebel wird geleert, und die Map endet nach #16/#19/#24.**

Die Destination („`CLAUDE.md` ist minimal und verlinkt nur") ist seit
[#33](https://github.com/mbalzert1978/fit_back/issues/33) erreicht — 58 Zeilen, keine Behauptung
über das Repo. Alles danach war Nebelverarbeitung, und die hat einen Selbstlauf: jede Auflösung
produziert neuen Nebel, der Nebel wird zu Tickets, die Tickets zu neuem Nebel. Sechs Flecken
standen zuletzt drin, und **jeder einzelne** war von der Bauart „wird scharf, sobald jemand misst" —
eine Maschine, die nie leerläuft.

`Not yet specified` wird geleert. Was dort stand, ist im Ticket-Verlauf und in diesem Doc
nachlesbar; wird eine der Fragen real, entsteht sie als normales Ticket neu. Nach #16, #19 und #24
wird die Map geschlossen.

## Die Lektion

**Eine erreichte Destination beendet eine Map nicht von selbst.** Niemand hat nach #33 gefragt, ob
die Map fertig ist, und der Nebel-Mechanismus liefert unbegrenzt Nachschub an plausibler Arbeit.
Der Fehler war nicht die Dauer, sondern das fehlende Zwischen-Halt: nach jeder Auflösung gehört die
Frage „ist die Destination damit erreicht?" gestellt, bevor der nächste Fleck aufgemacht wird.

**Und: Nebel gehört nie in `Out of scope`.** Der Abschnitt ist für Arbeit *hinter* dem Ziel. Was
dort landet, verschwindet aus jeder Abfrage. Bei #16/#19/#24 hat genau das drei Tickets begraben.
