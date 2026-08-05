# Kein externer Memory-Mechanismus — Entscheidungen liegen unter docs/decisions/

**Entschieden:** 2026-08-05 08:13

## Was

Für dieses Repository wird kein persistenter Memory-Mechanismus außerhalb des Repos genutzt
(weder Claude Codes sitzungsübergreifendes Memory-System noch irgendeine andere Notiz-Ablage
außerhalb des Repos) — weder für Entscheidungen noch für sonstige relevante Neuerungen. Das gilt
sowohl für das Anlegen neuer Einträge als auch für das Belassen bestehender — es soll keine
geben.

Entscheidungen und relevante Neuerungen werden stattdessen ausschließlich als Dateien unter
diesem Verzeichnis erfasst, eine Datei je Entscheidung, benannt `YYYY-MM-DD-HHMM-<slug>.md`.

## Warum

Hält das Repository als alleinige Quelle der Wahrheit dafür, warum die Dinge so sind, wie sie
sind — wer es klont (oder als Assistent in einer künftigen Sitzung darin arbeitet), sieht die
vollständige Entscheidungshistorie, ohne von einer separaten, schwerer teilbaren und schwerer
überprüfbaren Memory-Ablage abhängig zu sein.

## Was das ausschließt / ersetzt

- Eine versehentlich mitcommittete, fachfremde `MEMORY.md` (nebst einer weiteren Notizdatei) eines
  anderen, unabhängigen Projekts war unter `.claude/projects/` in diesem Repo gelandet — im Zuge
  dieser Entscheidung entfernt.
- [`docs/milestones/01-technical-decisions.md`](../milestones/01-technical-decisions.md) bleibt
  unverändert bestehen (sie dokumentiert die technische Rahmung der Backend-Portierung, kein
  Entscheidungslog) — neue Entscheidungen ab jetzt gehen unter `docs/decisions/`, nicht dort
  angehängt.
