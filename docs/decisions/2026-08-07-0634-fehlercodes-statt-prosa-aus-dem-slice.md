# Fehlercodes statt Prosa aus dem Slice — Uebersetzung ist Sache des HTTP-Randes

**Datum:** 2026-08-07, 06:34

## Problem

Ticket 0008 will Fehlertexte in de-DE und en-US ueber `Accept-Language` ausliefern
(`docs/Draft/BACKEND.md`, Abschnitt 0.9). Die deutschen Texte entstehen heute aber in **drei**
Schichten, und die Masse davon liegt **nicht** am HTTP-Rand:

- **Domaene** (7 Texte): die `parse`-Factories geben `Result[..., str]` mit fertiger deutscher
  Prosa zurueck — `not_empty_string.py:30`, `display_name.py:22`, `password.py:29`, `locale.py:42`,
  `password_hash.py:26`, `user_id.py:34`, `user_time_zone.py:34`.
- **Application** (14 Texte): `register_user/validators/register_user_rules.py`, Funktion
  `email_message` — der einzige Ort, der es schon richtig macht: `Email.parse` liefert die Tagged
  Union `EmailError`, die Application formuliert sie aus.
- **HTTP-Rand** (11 Texte): `api/identity/register_user_router.py`, `api/exception_handlers.py`,
  `api/problem_details.py`, `middleware/idempotency.py`.

Eine `Accept-Language`-Middleware am Rand erreicht die ersten beiden Gruppen nicht. Solange der Use
Case fertige Saetze zurueckgibt, ist er faktisch einsprachig.

## Entscheidung

**Der Slice gibt Fehlercodes plus Nutzlast zurueck, nie Prosa. Text entsteht ausschliesslich am
HTTP-Rand.**

Konkret:

1. Jede `parse`-Factory liefert eine **Tagged Union** als Fehlerfall, nicht `str` — genau nach dem
   Vorbild von `Email.parse`/`EmailError`. Die Nutzlast traegt, was die Meldung braucht (Maximum,
   ungueltige Zeichen, Rohwert), damit der Rand formulieren kann, ohne nachzufragen.
2. `email_message` und seine Geschwister entfallen in der Application. Der Response-Mapper
   uebersetzt Domaenenfehler in **Codes**.
3. Die public Response-Union des Use Case traegt ueber der Naht weiterhin **nur Primitive**, jetzt
   aber Code + Parameter statt eines Satzes. `RegistrationInvalid.errors` wird damit von
   `Mapping[str, tuple[str, ...]]` zu einer Feldfehler-Form aus Code und Parametern.
4. Der HTTP-Rand waehlt die Sprache (`Accept-Language`) und rendert Code + Parameter zu
   `title`/`detail`/`errors.*`.

## Warum nicht die Sprache in den Slice reichen

Die Alternative — die gewuenschte Sprache als Parameter in den Use Case geben — waere weniger
Umbau, macht aber einen Use Case von einer Praesentationsentscheidung abhaengig: jeder kuenftige
Aufrufer (Outbox-Consumer, Contract-Test, ein anderer Context ueber seinen Port) muesste eine
Sprache mitliefern, die ihn nichts angeht. Das widerspricht der Naht-Regel aus
`.rules/python/python-feature-slices.md` und dem Ziel, Contexts spaeter herausloesen zu koennen.

## Folgen

- **0008 wird groesser als bisher beschrieben** und fasst den Slice aus 0011 an: Response-Union,
  Test-API und die Specs unter `contexts/identity/specs/register_user/` ziehen mit.
- 0008 bekommt `Blocked by 0006` und `Blocked by 0011` zusaetzlich zu 0005.
- Der Fehler**code** ist ab dann der stabile Vertrag, der Text Kosmetik — das deckt sich mit dem
  bereits im Ticket festgehaltenen Befund, dass `type`/`code` sprachunabhaengig sind.
- Kuenftige Slices bauen ihre Fehlerfaelle von Anfang an als Tagged Union mit Nutzlast; die
  Referenzimplementierung `register_user` zeigt es nach dem Umbau durchgaengig statt nur bei Email.
