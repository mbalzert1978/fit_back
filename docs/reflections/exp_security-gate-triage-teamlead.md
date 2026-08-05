---
schema_version: 1
name: security-gate-triage-teamlead
description: Generische Security-Findings ohne Spezifikations-Basis werden vom Team-Lead selbst triagiert, nicht automatisch eskaliert oder blind umgesetzt
type: feedback
frequency: 2
last_triggered: 2026-08-05
decay_eligible: false
---

Ein Security-Gate-Finding aus `.rules/common/security.md` (generisches,
projektunabhaengiges Boilerplate, nie auf dieses Repo zugeschnitten) ist nicht
automatisch bindend, wenn nichts in `docs/Draft/BACKEND.md`/den Milestones es
fuer den jeweiligen Endpunkt/das jeweilige Ticket tatsaechlich verlangt. Der
Team-Lead triagiert selbst: Findings mit Basis in der Spezifikation und im
Scope des Tickets werden gefixt, Findings ohne Basis (z. B. Rate-Limiting/Auth
auf Endpunkten, fuer die kein Ticket geplant ist) werden bewusst gewaived und
dokumentiert — nicht blind umgesetzt und nicht automatisch an den Stakeholder
eskaliert.

**Why:** Dieses Muster wurde zweimal angewendet (Ticket 0001 und Ticket 0002)
und beide Male vom Nutzer implizit akzeptiert (keine Korrektur). Details:
[docs/decisions/2026-08-05-0936-security-gate-triage-ticket-0001.md](../decisions/2026-08-05-0936-security-gate-triage-ticket-0001.md),
[docs/decisions/2026-08-05-1130-security-gate-triage-ticket-0002-und-agent-integritaets-incident.md](../decisions/2026-08-05-1130-security-gate-triage-ticket-0002-und-agent-integritaets-incident.md).

**How to apply:** Bei jedem kuenftigen Security-Gate-Finding zuerst pruefen: (1)
Gibt es eine Basis in der Spezifikation? (2) Ist es im Scope dieses Tickets oder
fuer ein spaeteres Ticket vorgesehen? Nur bei „ja, im Scope" fixen; sonst waiven
und in einem Decision-Doc begruenden. Echte Produkt-/Scope-Fragen (nicht
generische Checklisten-Treffer) gehen weiterhin an den Stakeholder.
