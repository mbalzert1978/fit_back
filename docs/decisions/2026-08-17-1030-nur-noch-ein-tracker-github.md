# Nur noch ein Tracker: GitHub

**Map:** [#40 — Die Tickets des Backend-Baus](https://github.com/mbalzert1978/fit_back/issues/40)

## Was entschieden wurde

Der Markdown-Tracker `docs/issues/` ist abgeschafft. Die Tickets des Backend-Baus leben
ausschließlich als GitHub-Sub-Issues der Map [#40](https://github.com/mbalzert1978/fit_back/issues/40).
Damit hat dieses Repo **einen** Ticket-Ort statt zweier — Backend-Bau, Planung und Claude-Setup
liegen in derselben Ablage.

## Warum

Zwei Tracker nebeneinander waren nie eine Entscheidung, sondern ein Überbleibsel: die 50
Bau-Tickets wurden irgendwann nach GitHub gespiegelt, ohne dass die Markdown-Seite verschwand.
Danach gab es jeden Ticketstand zweimal — einmal im Frontmatter der Datei, einmal als
Issue-State plus Dependencies. Map #40 pflegte darüber hinaus eine handgeschriebene
Meilenstein-Tabelle mit allen 50 Zeilen, also eine **dritte** Kopie desselben Stands.

Dass das driftet, war bereits sichtbar: Der Body von #40 behauptete „sie hat keine
Kinder-Tickets und keine offenen Entscheidungen", während 50 Kinder daran hingen, und
`docs/agents/issue-tracker.md` führte unter „Live wayfinding efforts" noch „Keine" — Map #40
kam dort überhaupt nicht vor.

Die Spiegelung war vollständig und inhaltstreu, was den Schnitt billig machte: 50 lokale
Dateien ↔ 50 Sub-Issues, jedes mit Herkunftsbanner, vollem Body und auf absolute URLs
umgeschriebenen Links. Der einzige gemessene Unterschied waren die Blocked-by-Links in #51.

## Was dadurch ersetzt oder ausgeschlossen wird

**Gelöschte Skills.** Sie bedienten alle den lokalen Tracker; `gh` leistet dasselbe direkt:

- `issue-status` (→ `gh issue list`), `issue-close` (→ `gh issue close`)
- `to-issues` — hätte `docs/issues/` beim nächsten Lauf wieder angelegt
- `verify-issue-breakdown` und `audit-to-issues` — deren einzige Aufrufer `to-issues` war

`issues-to-prs` **bleibt**: es konsumiert nur bestehende Issues, kannte `docs/issues` nie und
läuft mit GitHub als Quelle unverändert weiter.

**Status und Blocking werden nicht mehr gepflegt, sondern abgeleitet.** GitHub trägt
Offen/Geschlossen und native Issue-Dependencies selbst. Die drei Werte, die früher im
Frontmatter standen, ergeben sich daraus: geschlossen → `closed`, offen mit offenen Blockern →
`blocked`, offen ohne → `open`. `architecture-adr-check` rechnet genau so; seine Verteilung über
die 50 Tickets (34 blockiert / 11 geschlossen / 5 offen) ist identisch mit der des alten
Frontmatters.

**Keine Statustabelle mehr in der Map.** Die Meilenstein-Tabelle in #40 ist ersatzlos gestrichen.
Eine handgepflegte Kopie dessen, was der Tracker selbst trägt, driftet zwangsläufig — sie war
schon einmal die Quelle des Widerspruchs oben.

**Historische Dokumente bleiben unangetastet.** `docs/decisions/` und `docs/reflections/`
verweisen an mehreren Stellen auf `docs/issues/` und die gelöschten Skills. Sie berichten, was
zu ihrer Zeit galt; sie nachzuschreiben würde sie verfälschen.

## Nebenbefund: die Frontier-Abfrage schnitt still ab

Die in `docs/agents/issue-tracker.md` hinterlegte, kanonische Frontier-Abfrage lief ohne
`--paginate` und sah damit nur die ersten 30 der 50 Kinder. Sie meldete **ein** offenes,
unblockiertes Ticket statt fünf — ohne Fehler und ohne Hinweis. Korrigiert in der Tracker-Doku
und im Body von #40; festgehalten als
[`exp_gh-api-paginate-schneidet-still-ab`](../reflections/exp_gh-api-paginate-schneidet-still-ab.md).

Der Fehler war latent, seit die Map über 30 Kinder hinauswuchs, und wäre ohne diesen Umbau
vermutlich unbemerkt geblieben: „eine Frontier" ist ein völlig normaler Zustand, also fällt
nichts auf.

## Nebenbefund: `gh` und der Proxy

Beim Einstieg lief jeder `gh`-Aufruf in einen TCP-Timeout auf `api.github.com`, während
`git fetch` im selben Moment funktionierte, und `gh auth status` meldete fälschlich
*„The token in keyring is invalid"*. Ursache: Der Egress-Proxy `127.0.0.1:3128` stand in der
git-Config und auf User-Ebene in der Windows-Umgebung — aber `HTTPS_PROXY`/`HTTP_PROXY` werden
aus der Prozessumgebung der Tool-Aufrufe entfernt (`NO_PROXY` aus derselben Quelle kommt durch).
Behoben über den `env`-Block in [`.claude/settings.json`](../../.claude/settings.json), der die
beiden Variablen für die Session setzt. Bemerkenswert: auf User-Ebene waren sie längst korrekt
gesetzt — sie werden gezielt aus der Prozessumgebung der Tool-Aufrufe entfernt, weshalb ein
`setx` das Problem nicht gelöst hätte.

Die Lehre ist die allgemeinere: **ein Verbindungsfehler ist kein Beweis über den Tracker.** Die
Sitzung stand kurz davor, aus „GitHub unerreichbar" auf „keine Map vorhanden" zu schließen —
derselbe Fehlschluss, vor dem `docs/agents/issue-tracker.md` bereits warnt („Look for the
artifact, not the configuration"), nur mit dem Netzwerk statt einer fehlenden Konfigurationsdatei
als Anlass.
