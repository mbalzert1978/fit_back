---
schema_version: 1
name: pruefkommando-muss-messen-was-es-behauptet
description: Ein Pruefkommando mit leerem Ergebnis beweist nichts, solange nicht gezeigt ist, dass es ueberhaupt greifen kann - Git-Pathspecs mit Glob liefern still falsch-negative Ergebnisse
type: feedback
frequency: 2
last_triggered: 2026-08-07
decay_eligible: false
---

Ein Kommando, dessen leere Ausgabe als Beleg dienen soll („kein Test angefasst", „keine
Verstoesse"), wird vor der Verwendung **gegen einen bekannten Treffer gehalten**. Erst wenn es
etwas findet, das es finden muss, ist seine Leere ein Beweis.

Konkreter Fallstrick: `git diff --stat main..HEAD -- 'src/contexts/*/specs'` liefert leer, obwohl
Dateien unter genau diesem Pfad geaendert sind. Mit direktem Pfad
(`-- src/contexts/identity/specs`) kommen sie. Fuer solche Belege deshalb entweder direkte Pfade
verwenden oder gegen `git diff --name-only main..HEAD` mit nachgeschaltetem `grep` pruefen.

**Why:** Beim Gate-Nachfahren zu Ticket 0048 habe ich dem Nutzer gemeldet, es sei „wirklich kein
Test angefasst" — belegt mit genau diesem Pathspec. Tatsaechlich hatte der Agent drei Docstrings
in zwei Spec-Dateien ergaenzt. Ich hatte den Bericht des Agenten misstrauisch geprueft und dabei
mein eigenes Pruefwerkzeug ungeprueft gelassen; herausgekommen ist eine Falschaussage mit dem
Gestus der Verifikation, was schlechter ist als gar keine Pruefung — sie beendet das Nachfragen.

Zwei weitere Fehlmessungen derselben Art folgten in derselben Sitzung: ein
`ruff check --select RUF100`, das zwangslaeufig jedes andere `noqa` als unbenutzt meldet (21
Scheintreffer), und ein `grep` auf einen Backslash, das am Shell-Escaping scheiterte. Beide
Ausgaben waren plausibel und falsch.

**How to apply:** Bei jedem Beleg, der auf einer leeren Ausgabe beruht: einmal absichtlich einen
Treffer erzeugen oder die Gegenprobe mit einem zweiten, anders gebauten Kommando fahren
(`--name-only` + `grep` statt Pathspec, direkter Pfad statt Glob). Im Bericht an den Nutzer das
verwendete Kommando mitschreiben, damit die Aussage nachpruefbar bleibt statt nur behauptet zu
sein. Dasselbe Prinzip wie bei fremden Gates, nur auf die eigenen Kommandos angewandt. Verwandt:
[[gruenes-gate-ohne-scope-angabe]], [[verify-subagent-progress-claims]].
