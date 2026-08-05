# Security-Gate-Triage für Ticket 0001: zwei Findings gewaived, eines behoben

**Entschieden:** 2026-08-05 09:36

## Was

Ticket 0001 ist nach 3 Fix-Verify-Durchläufen am Security-Gate eskaliert (siehe
[`2026-08-05-0839-implementation-pipeline-and-wave-1.md`](2026-08-05-0839-implementation-pipeline-and-wave-1.md),
Eskalationsregel). Als Team-Lead habe ich die drei gemeldeten Findings triagiert, statt sie
unbesehen an den Stakeholder weiterzureichen — das entspricht der vereinbarten Eskalationsstufe
„ich bewerte zuerst selbst, ziehe den Stakeholder nur bei echten Scope-/Produktfragen hinzu".

**Findings und Entscheidung:**

1. **„Rate limiting on all endpoints" fehlt auf `GET /api/v1/health`** (BLOCK laut
   Security-Review) — **gewaived für diesen Health-Endpoint.**
   Begründung: `docs/Draft/BACKEND.md` (die vollständige fachliche Spezifikation) und
   `docs/milestones/*.md` erwähnen Rate Limiting an keiner Stelle — weder als eine der 13
   Querschnitts-Regeln aus Abschnitt 0 noch in irgendeinem Ticket (per `grep` verifiziert). Die
   Regel stammt ausschließlich aus dem generischen, sprach-/projektunabhängigen
   `.rules/common/security.md` („Rate limiting on all endpoints" ist eine pauschale
   Allzweck-Checkliste, nicht auf dieses Repo zugeschnitten — anders als z. B. `qa-check`s
   `config.json`, die bereits früh an dieses Repo angepasst wurde). Ticket 0001 ist zudem
   explizit auf reines Repo-Skeleton beschränkt („Keine fachliche Logik über den Health-Endpoint
   hinaus implementieren"); Rate-Limiting-Middleware wäre ohnehin ein Cross-Cutting-Baustein für
   `shared_kernel` (analog Idempotency-Key-Middleware), der noch gar nicht existiert (kommt erst
   mit den M0-Shared-Kernel-Tickets 0004–0007) — ihn hier ad hoc in `main.py` nachzurüsten wäre
   Scope-Creep über das Ticket hinaus, nicht das Beheben eines Fehlers innerhalb des Tickets.
2. **`GET /api/v1/health` hat keine Authentifizierung** (LOW, vom Reviewer selbst als möglicher
   Sonderfall markiert) — **gewaived.** Unauthentifizierte Health-Probes sind Standardpraxis
   (Load-Balancer/Orchestrator-Zugriff ohne Credentials). `docs/Draft/BACKEND.md` scopt JWT-Auth
   explizit auf fachliche Endpunkte (Identity/M1), nicht auf Infrastruktur-Health-Checks.
3. **Exception-Details landen ungefiltert im Log** (`main.py`, DB-Verbindungsfehler/Health-Check-
   Fehler werden mit vollem Exception-Text geloggt) — **echtes, im Ticket-Scope behebbares
   Finding, wird gefixt.** Kein Scope-Creep: reine Log-Hygiene an bereits vorhandenem Code, kein
   neuer Baustein.

## Warum

Findings 1 und 2 prüfen gegen eine Anforderung, die in der fachlichen Spezifikation dieses
Projekts nirgends existiert und die, wenn sie je gewünscht wird, ein eigener
Cross-Cutting-Baustein in `shared_kernel` wäre (eigenes Ticket), nicht etwas, das rückwirkend in
ein bereits abgegrenztes M0-Bootstrap-Ticket gepresst wird. Finding 3 ist echte Log-Hygiene ohne
Scope-Ausweitung und wird daher behoben statt gewaived.

## Was das ausschließt / ersetzt

- Ersetzt keine bestehende Entscheidung, präzisiert aber die Anwendung von
  `.rules/common/security.md` für dieses Repo: das generische „Rate limiting on all endpoints"
  gilt nicht automatisch für jeden einzelnen Endpunkt unabhängig von fachlicher Spezifikation —
  sondern nur, wo `docs/Draft/BACKEND.md`/die Meilensteine es tatsächlich vorsehen. Taucht das
  Thema in einem späteren Ticket auf (z. B. wenn BACKEND.md an anderer Stelle doch Rate Limiting
  fordert), gilt diese Waiver-Begründung nicht automatisch weiter — dann neu bewerten.
- Schließt aus, dass ich diese Art von Findings künftig standardmäßig unbesehen an den
  Stakeholder eskaliere — vergleichbare Fälle (generische Regel ohne Rückhalt in der fachlichen
  Spezifikation, kein neues Ticket dafür vorgesehen) triagiere ich selbst nach demselben Muster.
