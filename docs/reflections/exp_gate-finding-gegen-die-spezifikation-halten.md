---
schema_version: 1
name: gate-finding-gegen-die-spezifikation-halten
description: Ein Gate-Finding wird gegen die Spezifikation geprueft, bevor es etwas ausloest - widerspricht es einer woertlich spezifizierten Entscheidung, wird es abgelehnt, nicht umgesetzt
type: feedback
frequency: 1
last_triggered: 2026-08-06
decay_eligible: false
---

Ein `BLOCK` ist ein Rohbefund, kein Auftrag. Vor jeder Umsetzung wird geprueft,
ob `docs/Draft/BACKEND.md` oder das Ticket den beanstandeten Punkt **woertlich
vorschreibt**. Tut es das, wird das Finding abgelehnt und die Ablehnung
begruendet - ein Gate darf keine Spezifikationsentscheidung umdrehen.

**Why:** In einer Runde aus fuenf parallelen Gates gegen einen fertigen Branch
lieferten zwei ein `BLOCK`, und **beide** wollten je eine woertlich
spezifizierte Entscheidung einem allgemeinen Prinzip opfern:

- Das Security-Gate wollte den `409` bei bereits vergebener E-Mail entfernen
  (Enumeration-Schutz) - `BACKEND.md` Zeile 124 schreibt
  `409 type=email-already-registered` woertlich vor. Der zweite Teil des
  Vorschlags, die Adresse aus dem `detail`-Text zu nehmen, aendert ausserdem
  nichts: der Angreifer hat sie selbst geschickt.
- Das Design-Gate wollte den `200` beim Idempotenz-Treffer auf den
  Originalstatus aendern und berief sich auf RFC 7231, die zum
  `Idempotency-Key` gar nichts sagt - `BACKEND.md` Abschnitt 0.3 schreibt „`200`
  statt `201`" woertlich vor.

Ein drittes Finding beanstandete einen ungenutzten `ttl_days`-Parameter als
Speculative Generality - er ist ein **Akzeptanzkriterium** von Ticket 0006.

Das Gegenstueck: der einzige wirklich schwere Fund der Runde stand in **keinem**
Bericht. Er entstand beim Nachpruefen dessen, was die Gates als „geprueft und in
Ordnung" abgehakt hatten. Vollstaendig in
[`docs/decisions/2026-08-06-1730-idempotenz-reservieren-statt-nachtragen.md`](../decisions/2026-08-06-1730-idempotenz-reservieren-statt-nachtragen.md).

**How to apply:** Jedes Finding vor der Umsetzung an der Quelle pruefen - im
Zweifel die Zeile in `BACKEND.md` oder im Ticket aufschlagen und zitieren. Drei
Ablehnungsgruende wiederholen sich: (1) die Spezifikation schreibt genau das
Gegenteil vor, (2) das Finding beruft sich auf eine Norm, die den Fall nicht
regelt, (3) der beanstandete Code ist ein Akzeptanzkriterium. Den Gates
umgekehrt schon im Auftrag mitgeben, was im Repo als gut gilt (`Result` statt
Exceptions, `Timestamp` statt `datetime`, keine Abstraktion ohne zweiten
Nutzer) - sonst schlagen sie zuverlaessig vor, genau diese Entscheidungen
zurueckzudrehen. Verwandt: [[security-gate-triage-teamlead]] (Findings **ohne**
Spezifikations-Basis waiven - hier geht es um Findings, die ihr **widersprechen**),
[[review-agent-null-findings-ist-kein-freibrief]].
