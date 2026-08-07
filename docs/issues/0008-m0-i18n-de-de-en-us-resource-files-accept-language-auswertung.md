---
id: "0008"
title: M0: i18n - de-DE/en-US Resource-Files + Accept-Language-Auswertung
status: open
milestone: M0
type: AFK
---

# M0: i18n - de-DE/en-US Resource-Files + Accept-Language-Auswertung

## Parent

Meilenstein [M0](docs/milestones/m0-projekt-grundgeruest.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Resource-Files-Mechanismus fuer Fehlermeldungen/serverseitige Texte in de-DE (Default) und en-US, ausgewaehlt ueber den Accept-Language-Header (Abschnitt 0.9).

## Stand: zurueckgestellt ans Ende, PR #9 geschlossen

Ein erster Anlauf (Branch `0008-…`, PR #9) wurde **geschlossen, nicht gemergt**. Kerndefekt:
`src/shared_kernel/i18n/middleware.py` und `src/shared_kernel/resources/provider.py` legten eine
Starlette-Middleware und dateibasiertes Ressourcen-Laden in die dependency-freie Domaenenschicht;
zusaetzlich verletzte der Code durchgaengig die Stilregeln (kein Pattern Matching, Exceptions statt
`Result`, imperativ statt deklarativ). Der Branch bleibt als Vorlage erhalten.

**Platzierung beim Neubau:** Sprachauswahl ist **kein** Kerngeschaeft, sondern ein
Praesentations-/Infrastruktur-Anliegen — Accept-Language ist ein HTTP-Protokollbelang (RFC 7231),
die Middleware ist Framework-gekoppelt, das Laden der Resource-Files ist Datei-IO. Nichts davon
gehoert in `shared_kernel`. Der `domain-purity`-Contract in `setup.cfg` erzwingt das inzwischen
maschinell fuer die Context-Domaenen.

**Einplanung: ganz ans Ende.** Nachweislich blockiert dieses Ticket **kein einziges** anderes
(`grep -l "Blocked by \[0008\]" docs/issues/*.md` liefert nichts). Fehlercodes wie
`email-already-registered` sind der API-Vertrag und sprachunabhaengig; lokalisierte `title`/`detail`
sind Kosmetik und koennen jederzeit nachgezogen werden.

Dass ein M0-Ticket damit auf ein M1-Ticket (0011) wartet, ist gewollt und die Konsequenz dieser
Zurueckstellung: der Meilenstein-Schnitt hat hier keine Steuerungswirkung mehr, weil 0008 selbst
nichts blockiert.

## Der eigentliche Umfang: 34 fest verdrahtete deutsche Texte in 9 Dateien

Die Ueberschrift „Resource-Files + Accept-Language" verdeckt, wo die Arbeit wirklich liegt. Deutsche
Prosa entsteht heute in **drei** Schichten, und der groessere Teil davon **nicht** am HTTP-Rand —
eine Middleware am Rand erreicht ihn also nicht:

| Schicht | Ort | Texte |
| --- | --- | --- |
| Shared Kernel | `src/contexts/shared_kernel/not_empty_string.py:30` | 1 |
| Domaene | `identity/domain/value_objects/`: `display_name.py:22`, `password.py:29`, `locale.py:42`, `password_hash.py:26`, `user_id.py:34`, `user_time_zone.py:34` | 6 |
| Application | `identity/application/register_user/validators/register_user_rules.py`, Funktion `email_message` | 14 |
| HTTP-Rand | `api/identity/register_user_router.py:103,110,111`; `api/exception_handlers.py:40,42`; `api/problem_details.py:45,49` (OpenAPI-Beispiele); `middleware/idempotency.py:319,320,329,330`; `middleware/unhandled_exceptions.py:64,68` | 13 |

`Email.parse` ist der einzige Ort, der es schon richtig macht: es liefert die Tagged Union
`EmailError` mit Nutzlast, und erst die Application formuliert daraus einen Satz. Alle anderen
`parse`-Factories geben `Result[..., str]` mit fertigem deutschem Text zurueck.

## Grundsatzentscheidung (2026-08-07)

**Der Slice gibt Fehlercodes plus Nutzlast zurueck, nie Prosa; uebersetzt wird ausschliesslich am
HTTP-Rand.** Vollstaendig begruendet in
[`2026-08-07-0634-fehlercodes-statt-prosa-aus-dem-slice.md`](../decisions/2026-08-07-0634-fehlercodes-statt-prosa-aus-dem-slice.md).
Die Alternative — die Sprache in den Use Case hineinreichen — ist geprueft und verworfen.

Daraus folgt: **dieses Ticket fasst den Slice aus 0011 an** (Response-Union, Test-API, Specs). Es
ist keine reine Randarbeit mehr.

## Verbindliche Festlegungen

Damit niemand sie beim Bauen neu erfinden muss:

- **`Accept-Language` entscheidet die HTTP-Antwort, immer** — auch bei authentifizierter Anfrage.
  `User.Locale` (`docs/Draft/BACKEND.md:99`) ist die Praeferenz fuer serverseitig **ohne** HTTP-
  Anfrage erzeugte Texte (E-Mails, Benachrichtigungen aus Outbox-Consumern) und wird am HTTP-Rand
  **nicht** herangezogen. Sonst brauchte jeder Fehlerfall am Rand einen Datenbankzugriff, nur um
  eine Sprache zu waehlen.
- **Header-Auswertung nach RFC 7231:** q-Gewichte werden ausgewertet, hoechstes gewinnt; bei
  Gleichstand die zuerst genannte Sprache. Ein reiner Regionstreffer zaehlt (`de-AT` ⇒ `de-DE`,
  `en-GB` ⇒ `en-US`). `*` bedeutet Default. Unbekannte Sprache, `q=0` auf allen bekannten, leerer
  oder syntaktisch defekter Header ⇒ **de-DE**, niemals ein Fehler: die Sprachwahl darf eine sonst
  gueltige Anfrage nie scheitern lassen.
- **Resource-Files:** je Sprache eine Datei unter `src/api/resources/` (Praesentationsschicht, nicht
  `shared_kernel` — der `domain-purity`-Contract erzwingt das inzwischen maschinell), Format `.json`,
  flache `code -> Vorlage`-Abbildung, Platzhalter als benannte Felder (`{maximum}`, `{label}`) aus
  der Fehler-Nutzlast. Geladen wird einmal beim Start, nicht je Anfrage.
- **Fehlender Code:** ist zu einem Code in einer Sprachdatei keine Vorlage hinterlegt, faellt der
  Text auf de-DE zurueck; fehlt er auch dort, ist das ein Startfehler, kein Laufzeitfehler — beim
  Hochfahren wird geprueft, dass jede Sprachdatei dieselbe Code-Menge abdeckt.

## Acceptance criteria

Flach, ohne Stufengliederung: Praesentations-/Infrastruktur-Arbeit ohne eigene Fachregel, siehe
[`00-overview.md`](../milestones/00-overview.md), „Ticket-Schnitt".

**Umbau (Voraussetzung fuer alles Weitere)**

- [ ] Jede `parse`-Factory liefert im Fehlerfall eine **Tagged Union** mit Nutzlast statt eines
      `str` — Vorbild `Email.parse`/`EmailError`. Betroffen: die 7 Stellen in Shared Kernel und
      Domaene aus der Tabelle oben. Die Form ist seit dem 2026-08-07 verbindliche Regel, siehe
      `.rules/python/python-error-handling.md`, Abschnitt „Die Fehlernutzlast ist ein typisierter
      Fall, nie ein fertiger Satz" — dieses Ticket zieht den Bestand nach, es erfindet die Form
      nicht.
- [ ] Die public Response-Union von `register_user` traegt ueber der Naht Code + Parameter statt
      eines Satzes (`RegistrationInvalid.errors` aendert seine Form); Test-API und die Specs unter
      `contexts/identity/specs/register_user/` ziehen mit. `email_message` entfaellt.
- [ ] Alle 34 bestehenden Texte sind migriert — keiner bleibt inline im Code stehen. Der Nachweis
      ist ein Test, der die Quelldateien der drei nicht-Rand-Schichten auf verbleibende deutsche
      Prosa in Rueckgabewerten prueft (Kommentare und Docstrings bleiben deutsch, siehe CLAUDE.md).

**Verhalten**

- [ ] Derselbe Domaenenfehler liefert je nach `Accept-Language` `title` und `detail` auf Deutsch
      oder Englisch
- [ ] Dasselbe gilt fuer **Feldfehler** (`errors.*`) — sie machen mit 20 von 34 Texten die Masse aus
      und sind der eigentliche Pruefstein
- [ ] Fehlt der Header, ist de-DE der Default; die vier Sonderfaelle oben (unbekannt, `q=0`, leer,
      defekt) sind je durch einen Test belegt
- [ ] `type` und der Fehlercode sind **sprachunabhaengig** — nachgewiesen durch einen Test, der
      dieselbe Anfrage zweisprachig stellt und identische `type`/`code`-Werte, aber verschiedene
      `title`/`detail` erwartet
- [ ] Die Antwort traegt `Content-Language` mit dem tatsaechlich gewaehlten Tag (`de-DE`/`en-US`)
- [ ] Neue Fehlertexte werden zentral in den Resource-Files gepflegt, nicht inline im Code

## Blocked by

- Blocked by [0005](0005-m0-shared-kernel-rfc-7807-problemdetails-exception-handler.md)
- Blocked by [0006](0006-m0-shared-kernel-idempotency-key-middleware-shared-idempotency-keys.md) — vier der Texte liegen in dieser Middleware
- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md) — 20 der Texte liegen in dessen Slice; die Response-Union, die hier umgebaut wird, entsteht dort
