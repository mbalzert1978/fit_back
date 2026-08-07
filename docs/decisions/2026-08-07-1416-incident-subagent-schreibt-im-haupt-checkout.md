# Vorfall: Sub-Agent des Entwickler-Agenten schrieb im Haupt-Checkout

**Datum:** 2026-08-07, 14:16
**Ticket:** 0048 (ruff auf Production-Level für `src/`)
**Status:** bereinigt, Arbeit gerettet, Gegenmaßnahme festgelegt

## Was passiert ist

Der für Ticket 0048 gestartete Entwickler-Agent bekam — wie von
[`exp_workflow-agent-cd-explizit.md`](../reflections/exp_workflow-agent-cd-explizit.md)
gefordert — als allerersten Schritt ein explizites
`cd <worktree>` in seinem Prompt und in `Task.md`. Er hat sich daran gehalten: die
Konfigurationsänderung an `pyproject.toml` und die Docstrings in den `src/`-Modulen
entstanden korrekt im Worktree `0048-ruff-production-level`.

Für die reine Fleißarbeit (`D103`/`D104`, 45 Verstöße) hat er dann jedoch **selbst einen
Sub-Agenten gestartet**. Dieser Sub-Agent erbte die `cd`-Anweisung nicht und lief im
Standard-Arbeitsverzeichnis — dem **Haupt-Checkout auf `main`**. Dort veränderte er 34
Dateien (11 unter `alembic/*/versions/`, 23 `__init__.py` und Modul-Dateien unter `src/`).

Aufgefallen ist es dem Nutzer, nicht der Pipeline.

## Schadensumfang

- **Keine Commits.** `git reflog` auf `main` zeigt nach `pull --tags origin main`
  (`bba1f4d`) keinen weiteren Eintrag; `git rev-list --left-right --count origin/main...HEAD`
  war und ist `0 0`. Es war ausschließlich der Arbeitsbaum betroffen.
- Kein Push, kein PR, keine Manipulation an Kontroll-Infrastruktur (Skill-Configs,
  Hooks, `.rules/`) — `git status` listete nur `src/` und `alembic/`.

## Bereinigung (verifiziert, nicht blind)

1. Agent über `TaskStop` beendet, bevor er committen konnte.
2. Inhalt der Änderungen geprüft: es war echte 0048-Arbeit (`"""Upgrade database
   schema."""` u. Ä.), nicht Fremdes.
3. Änderungen als Patch gesichert (`git diff -- src alembic`), geprüft dass **kein**
   `docs/`-Pfad enthalten ist — die einzige legitime Änderung im Haupt-Checkout war der
   `issue-close`-Vermerk für 0008.
4. Patch im Worktree angewendet (`git apply --check` vorab, sauber). Die Dateimengen von
   Haupt-Checkout und Worktree waren disjunkt — nichts überschrieben, nichts doppelt.
5. Haupt-Checkout mit `git checkout -- src alembic` zurückgesetzt. Endzustand: nur noch der
   0008-`issue-close`-Vermerk modifiziert, `HEAD` unverändert `bba1f4d`, `0 0` gegen
   `origin/main`.

## Root Cause

Die bestehende Regel adressiert den **direkt gestarteten** Agenten. Sie sagt nichts über
Agenten, die dieser seinerseits startet. Ein Sub-Agent bekommt einen frisch initialisierten
Kontext und damit das Standard-Arbeitsverzeichnis des Haupt-Checkouts — die `cd`-Anweisung
des Elternteils wirkt nicht transitiv.

Damit ist die Absicherung „`cd` als erster Schritt im Prompt" **nicht vollständig**: sie
sichert genau eine Ebene ab und lässt jede darunter offen.

## Gegenmaßnahme

Sub-Agenten bleiben **erlaubt** — Parallelität ist ausdrücklich gewollt. Ein Verbot wäre die
falsche Konsequenz gewesen: es hätte das eigentliche Problem (fehlende Ortsangabe nach unten)
nur zugedeckt und den erwünschten Nutzen mitgenommen. Stattdessen gelten für jede Delegation
zwei Bedingungen, beide im Implementierungs-Brief verankert:

1. **Ortsangabe wird weitergereicht.** Jeder Prompt an einen Sub-Agenten beginnt mit derselben
   expliziten `cd <worktree>`-Anweisung, die der Elternteil bekommen hat. Ein Sub-Agent erbt
   das Arbeitsverzeichnis nicht.
2. **Delegieren heißt parallel arbeiten, nicht dirigieren.** Wer Arbeit abgibt, behält
   gleichzeitig ein eigenes Arbeitspaket. Ein Agent, der vier Sub-Agenten beauftragt und
   selbst wartet, hat nichts parallelisiert — er hat nur eine Ebene Latenz und eine Ebene
   Kontrollverlust eingezogen. Der Schnitt muss disjunkt sein (Dateimengen, die sich nicht
   überlappen), sonst entstehen genau die Konflikte, die Parallelität einsparen soll.

Ergänzend, unabhängig davon: nach jedem Agentenlauf, der einen Worktree betrifft, ist
`git status --short` im **Haupt-Checkout** zu prüfen, nicht nur im Worktree. Das ist die
Kontrolle, die den Vorfall gefunden hätte — und sie greift auch bei Fehlern, die diese beiden
Regeln nicht abdecken.

Instruktionen an Agenten werden künftig über den Skill `refine-prompt` gehärtet, statt frei
formuliert zu werden.

## Randbefund (kein Teil des Vorfalls)

Die vom Sub-Agenten erzeugten Docstrings sind englisch (`"""Initialize catalog context."""`),
während die vorhandenen Kommentare desselben Repos deutsch sind
(`# UUIDv7: Identitaet und Reihenfolge in einer Spalte`). Ob Docstrings unter die
Sprachregel von [`CLAUDE.md`](../../CLAUDE.md) fallen oder unter „Code, Bezeichner und
Kommentare folgen den üblichen Sprachkonventionen für Quellcode", ist offen und gehört ins
QA-Gate von 0048 — nicht hierher.
