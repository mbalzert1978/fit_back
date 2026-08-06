# Repo-Layout geschärft und der Einstiegspunkt auf seine eine Aufgabe reduziert

**Entschieden:** 2026-08-06, 16:20 — im Review der Struktur nach dem ersten vollständigen Slice.

## Die Verschiebungen

| vorher | nachher | warum |
|---|---|---|
| `src/shared_kernel/` | `src/contexts/shared_kernel/` | Der Shared Kernel ist das **geteilte Modell der Contexts**, kein Rahmenwerk daneben. Auf gleicher Höhe mit `api/` und `infrastructure/` las er sich wie eine technische Schicht; er ist aber Domänen-Vokabular. |
| `src/shared_infrastructure/` | `src/infrastructure/` | Das `shared_` war Gegenstück zu `shared_kernel`. Ohne dieses Gegenüber trägt es nichts mehr: es gibt genau eine kontextübergreifende Infrastruktur. |
| `src/shared_infrastructure/idempotency.py` | `src/middleware/idempotency.py` | Eine ASGI-Middleware ist keine Infrastruktur, sondern ein Glied der Anfrage-Kette. Sie lag nur dort, weil sie eine Tabelle anfasst — dann müsste jeder Slice auch dorthin. |
| `Settings`, `validate_settings` aus `main.py` | `src/settings.py` | Die Konfiguration wird auch von Dingen gebraucht, die die App nicht hochfahren. |
| Health-Endpunkt aus `main.py` | `src/api/health_router.py` | Ein Endpunkt ist ein Router, kein Bestandteil des Zusammenbaus. |

## Was `main.py` jetzt noch ist

Nur noch der Zusammenbau, und der beantwortet zwei Fragen: **woraus besteht die Anwendung**
(Middleware, Handler, Router — alles auf Modulebene) und **was lebt so lange wie der Prozess**
(Engine, Ereignis-Registrierung, Outbox-Worker — der Lifespan, und der legt nur an und räumt weg).

Die Trennung ist keine Kosmetik: dass Gestalt auf Modulebene gehört, ist genau die Regel, deren
Verletzung die Anwendung startunfähig gemacht hatte
([`2026-08-06-1500`](2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md)).

## Neu: ein Auffangpunkt für unbehandelte Ausnahmen

`src/middleware/unhandled_exceptions.py`. Sie ist **kein Fehlerkanal** — fachliche Fehlausgänge
tragen die Slices in ihrer Response-Union. Was hier ankommt, ist per Definition kein Fachfall,
sondern ein Programmierfehler oder eine ausgefallene Ressource.

Sie ersetzt Starlettes eingebauten `ServerErrorMiddleware`, der in Produktion eine nackte
`Internal Server Error`-Textantwort liefert — ohne Format und ohne dass der Stacktrace irgendwo
mit Kontext festgehalten wäre. Ein Aufrufer, der überall sonst `application/problem+json`
bekommt, bekäme ausgerechnet im schlimmsten Fall etwas anderes.

Zwei Zusagen, und die zweite ist die wichtigere:

1. Der Fehler steht **vollständig im Log** — mit Stacktrace, Methode und Pfad.
2. **Nichts davon steht in der Antwort.** 500 als RFC-7807-Dokument ohne Details. Ein Stacktrace
   nach außen verrät Dateipfade, Bibliotheksversionen und oft genug Teile der Nutzdaten; ein Test
   prüft genau das.

Sie liegt **außen** vor der Idempotenz-Prüfung — sonst sähe sie nicht, was weiter innen hochkommt,
auch nicht aus dieser selbst.

## `not_blank` trimmt jetzt

`NotEmptyString.parse` lautete `not_blank(raw).map(lambda text: cls(text.strip()))`, während
`not_blank` intern schon `raw.strip()` auswertete — aber nur als Prädikat und dann verwarf, um
`Ok(raw)` zurückzugeben. Zweimal dieselbe Arbeit, und die zweite an einer Stelle, die jeder
weitere Aufrufer von `not_blank` vergessen kann: Wer die Regel in einer `chain(...)` verwendet,
bekam ungetrimmten Text und hätte selbst nachtrimmen müssen.

Jetzt gibt `not_blank` den getrimmten Text zurück, und `parse` ist `not_blank(raw).map(cls)`.

## Was das ausschließt

- Kein weiteres Top-Level-Paket neben `api/`, `middleware/`, `infrastructure/`, `contexts/`. Was
  neu entsteht, gehört in eines davon oder braucht eine eigene Entscheidung.
- Keine Fachlichkeit und keine Konfiguration in `main.py`.
- Der `domain-purity`-Contract verbietet dem Shared Kernel jetzt zusätzlich `src.api`,
  `src.middleware`, `src.main` und `src.settings` — nicht nur externe Pakete. Damit kann er nicht
  durch die Hintertür an ein Framework geraten.
