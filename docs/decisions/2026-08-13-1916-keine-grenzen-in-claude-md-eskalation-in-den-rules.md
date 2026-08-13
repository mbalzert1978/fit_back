# Kein Grenzen-Abschnitt in `CLAUDE.md` — die Regel steht als Eskalationsregel in `.rules/`

**Datum:** 2026-08-13, 19:16
**Ticket:** [#23 — Grenzen-Abschnitt in CLAUDE.md](https://github.com/mbalzert1978/fit_back/issues/23)
**Map:** [#25 — Hook-Portfolio und semble-Anbindung des Claude-Setups](https://github.com/mbalzert1978/fit_back/issues/25)

## Das Ticket dreht sein Ergebnis um

Das Ticket wollte einen Abschnitt in `CLAUDE.md` mit drei Stufen (immer erlaubt / vorher fragen /
nie) und mindestens fünf aus `docs/reflections/` belegten „Nie"-Punkten. Entschieden ist das
Gegenteil: **`CLAUDE.md` bekommt keinen Abschnitt.** Übrig bleibt genau eine Regel, und die steht
eine Ebene tiefer.

## Was entschieden wurde

**1. Nur die „Nie"-Stufe ist überhaupt eine Regel für Prosa.**

„Immer erlaubt" und „vorher fragen" sind maschinell entscheidbar und haben in diesem Repo bereits
einen Ort: den `permissions`-Block in `.claude/settings.local.json`. Eine Prosa-Kopie daneben ist
die Bauart, die
[`exp_maschinelle-absicherung-statt-review-regel.md`](../reflections/exp_maschinelle-absicherung-statt-review-regel.md)
verbietet, und sie driftet still, sobald jemand die Settings ändert. Das Aufräumen der Permissions
selbst ist [#16](https://github.com/mbalzert1978/fit_back/issues/16) und liegt außerhalb dieser Map.

**2. Kein Punktekatalog, keine Mindestzahl.**

Das Abnahmekriterium „mindestens fünf belegte Punkte" ist gestrichen. Eine Mindestzahl lädt zum
Auffüllen ein und arbeitet damit gegen ein Ziel, das kürzen will. Von den 41 Lektionen in
`docs/reflections/` sind die meisten Handgriffe, keine Grenzen; ein Katalog hätte sie vermischt.

**3. Kein zweiter Reflections-Index.**

[`docs/reflections/README.md`](../reflections/README.md) ist bereits die kompakte Liste — 41
Einträge, je eine Zeile. Und der Nudge dorthin steht schon in `CLAUDE.md` („Vor einer neuen Welle
die `README.md` dort lesen."). Ein zweiter Index wäre eine zweite Wahrheit über dieselben Dateien.

**4. Die eine verbliebene Regel: bei Unschlüssigkeit nicht raten.**

Sie steht als neue Datei [`.rules/common/escalation.md`](../../.rules/common/escalation.md) und hat
zwei Hälften:

- **Mit Mensch in der Schleife:** fragen, bevor entschieden wird.
- **Ohne Mensch** (Worktree, Ticket-Pipeline, Hintergrundagent): anhalten, die Unschlüssigkeit
  benennen, den beauftragenden Agenten auffordern, sie an den Menschen zu dirigieren.

Dazu die Kette nach oben: Jede Ebene entscheidet nur, was sie aus eigenem Kontext ohne Raten
entscheiden kann. Eine Ebene höher zu sitzen erlaubt keine Annahme, die eine Ebene tiefer verboten
war.

**Warum eine eigene Datei:** `.rules/common/agents.md` wäre der topische Platz gewesen und ist in
derselben Sitzung gelöscht worden (siehe unten). Die übrigen Dateien passen thematisch nicht. Eine
Regel in eine Datei zu legen, die als nächstes fällt, verliert sie wieder.

**Warum in `.rules/` und nicht in `CLAUDE.md`:** `CLAUDE.md` verlinkt `.rules/` als die verbindlichen
Standards. Der Einwand dagegen ist notiert und wurde überstimmt: `CLAUDE.md` ist die einzige Datei,
die jede Sitzung automatisch lädt, `.rules/` wird nur gelesen, wenn jemand hinschaut. Sollte die
Regel in der Praxis nicht greifen, ist das die Stelle, an der nachgebessert wird.

## Was dabei mit `.rules/` passiert ist

Im Verlauf des Grillings fielen drei Dateien als Fremdvorlagen auf, die Dinge vorschrieben, die es
in diesem Repo nicht gibt. Markus hat sie in derselben Sitzung gelöscht:

- `common/agents.md` — listete elf Agenten in `~/.claude/agents/` (planner, architect,
  rust-reviewer, harmonyos-app-resolver); dieses Repo hat drei, und die liegen in `.claude/agents/`.
- `common/development-workflow.md` — schrieb die Agenten planner, tdd-guide und code-reviewer vor,
  verlangte Recherche über Context7 und Exa (nicht installiert) und verwies auf ADRs und PRDs.
- `common/code-review.md`, `common/hooks.md`, `common/testing.md` — ebenfalls entfernt.

Damit ist `.rules/` von Fremdinfrastruktur zu repo-eigener Dokumentation geworden. Die
Sprachregelung aus `CLAUDE.md` greift ab jetzt: **`.rules/common/` und `.rules/README.md` sind auf
Deutsch übersetzt**; `.rules/python/` war es bereits. Der Index in `.rules/README.md` war zusätzlich
veraltet — er listete gelöschte Dateien, ein `csharp/`-Verzeichnis, ein nicht existierendes
`skills/` und eine Reihe nie vorhandener Sprachverzeichnisse — und ist gegen den Ist-Zustand neu
geschrieben.

Eine inhaltliche Änderung über die Übersetzung hinaus: die Benennungsregeln in
`common/coding-style.md` schrieben `camelCase` und „custom hooks mit `use`-Präfix" vor — JavaScript
und React, in einem Python-Repo schlicht falsch. Sie sind auf das reduziert, was sprachunabhängig
gilt.

## Was dadurch ausgeschlossen ist

- Kein `## Grenzen`-Abschnitt in `CLAUDE.md`, jetzt nicht und nicht als kleinere Variante.
- Keine Liste erlaubter oder nachfragepflichtiger Aktionen in Prosa.
- Keine zweite Übersicht über `docs/reflections/`.
