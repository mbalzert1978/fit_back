# Der Refresh-Token ist ein Aggregat — die Lebensdauern ziehen nach innen

## Was entschieden wurde

`RefreshToken` wird als eigenes Aggregat in der Domäne modelliert (BACKEND.md Abschnitt 1), mit
genau den Feldern, die die heutige Tabelle `identity.refresh_tokens` hat. Der Name `Session` fällt:
er stand für zwei verschiedene Dinge.

| neu | was es ist |
|-----|------------|
| `domain/entities/refresh_token.py` | `RefreshToken` — Aggregat, dazu `issue` als benannter Konstruktor |
| `domain/value_objects/refresh_token_id.py` | `RefreshTokenId` — UUIDv7, nur `generate` |
| `domain/value_objects/token_hash.py` | `TokenHash` — der Abdruck, nie der Klartext |
| `domain/value_objects/issued_credentials.py` | `IssuedCredentials` — was der Nutzer mitbekommt |
| `domain/token_lifetimes.py` | `ACCESS_TOKEN_LIFETIME`, `REFRESH_TOKEN_LIFETIME` |

Gelöscht: `domain/value_objects/session.py` und der Naht-Typ `IssuedSession`.

Umgeformt: statt **einer** Operation, die alles zugleich tat, stehen jetzt zwei Nähte —
`abstractions/session_tokens.py` mit `mint_secret` und `store` samt den beiden Datensätzen
(`MintedSecret`, `RefreshTokenRecord`), und `abstractions/access_tokens.py` mit `sign`.

Nachgezogen: `SessionIssuerAdapter`, `Registration` (`credentials` statt `session`), der
Response-Mapper, der Fake, `PostgresSessionTokens`, `JwtAccessTokens`.

Unangetastet: die HTTP-Antwort, sämtliche Specs, das beobachtbare Verhalten der Test-API
(`issued_refresh_tokens`) und das Datenbankschema — **keine Migration**.

## Warum die alte Form falsch war

**Ein Aggregat wurde in der Infrastruktur gebaut.** `uuid7()`, der SHA-256-Abdruck und
`issued_at + 60 Tage` entstanden alle in `postgres_session_tokens.py`. Damit lag die Frage „was ist
ein gültiger Refresh-Token" in der äußersten Schicht — und als lose Primitive, was BACKEND.md
Abschnitt 0, Punkt 10 für Aggregate und Entitäten ausschließt.

**Ein Name für zwei Dinge.** `Session` hieß auf der Innenseite ein Value Object mit vier
Primitiven. Darin steckte der Refresh-Token im **Klartext**. Das Aggregat dagegen hält den
**Abdruck** und wird abgelegt. Beides unter einem Wort zu führen, verdeckte genau den Unterschied,
auf dem die Sicherheit beruht
([`pyjwt` hinter der Naht](2026-08-21-2230-pyjwt-hinter-der-naht-refresh-token-als-hash.md)).
Jetzt heißen sie `RefreshToken` und `IssuedCredentials`.

**Die Lebensdauern standen dreimal da.** 900 und 5 184 000 lagen in `jwt_access_tokens.py`, in
`postgres_session_tokens.py` und noch einmal abgeschrieben im Fake. Wie lange ein Zugang gilt, ist
eine fachliche Zusage (BACKEND.md Abschnitt 0, Punkt 8), kein Detail des Signaturverfahrens. Sie
stehen jetzt einmal, in `domain/token_lifetimes.py`. Der Fake braucht sie gar nicht mehr, und der
Signierer bekommt sein Zeitfenster übergeben statt es selbst auszurechnen.

## Warum der `User` keine `SessionId` hält

Der Verweis geht in **eine** Richtung: der Token nennt seinen Nutzer, der Nutzer kennt keinen
Token. Ein Nutzer hat viele Sitzungen; jede Rotation erzwänge sonst ein Update der Nutzer-Zeile,
und nach einem Logout zeigte `User` auf einen toten Token. Die Datenbank modelliert es bereits so
(`refresh_tokens.user_id → users.id`, kein `users.session_id`).

## Warum nur die heutigen Spalten

Kein `revoked_at`, kein `replaced_by` — obwohl BACKEND.md sie nennt. Beide bekommen mit Ticket
[#53](https://github.com/mbalzert1978/fit_back/issues/53) (RefreshSession, Rotation und
Reuse-Detection) ihren ersten Aufrufer. Vorher wären sie Felder, die niemand liest und
niemand schreibt: Spekulation, die das Aggregat mit einem Zustand belastet, den keine Regel prüft.
Dieselbe Begründung für `RefreshTokenId`: nur `generate`, kein `parse` und kein `hydrate`, weil
heute niemand einen Token aus der Ablage zurückholt.

## Warum zwei Nähte und nicht eine

Die Regel „je Mitspieler ein eigener Vertrag" zählt Mitspieler, nicht Operationen — und es sind
**zwei**: die Ablage (`PostgresSessionTokens`) und der Signierer (`JwtAccessTokens`). Sie teilen
nichts: die eine hält die laufende Transaktion, der andere das Signaturgeheimnis.

Zunächst standen beide in **einem** Vertrag, erfüllt von `PostgresSessionTokens`, das `sign` nur
an `JwtAccessTokens` weiterreichte. Genau das ist der Middle Man, den die Regel verhindern soll:
eine Methode, die nichts beiträgt, nur damit die Zählung „ein Mitspieler" aufgeht.

Also zwei Verträge: `RegisterUserSessionTokens` (Geheimnis ziehen, Zeile schreiben) und
`RegisterUserAccessTokens` (signieren). Der Signierer erfüllt seinen unmittelbar, die Weitergabe
entfällt. Die Transaktions-Zusage bleibt davon unberührt — sie hängt an der Ablage, und die ist
weiterhin ein Mitspieler mit einem Vertrag.

## Was der Adapter jetzt tut — und warum das kein Orchestrieren ist

`SessionIssuerAdapter.issue` ruft drei Naht-Operationen — zwei an der Ablage, eine am Signierer —
und dazwischen `RefreshToken.issue`. Das
sieht nach Ablauf aus, ist aber die Übersetzung **einer** fachlichen Handlung: „stelle diesem
Nutzer Zugangsdaten aus". Der Fachablauf des Use Case steht weiterhin vollständig im Handler
([Die Sitzung entsteht im Handler](2026-08-27-1630-die-sitzung-entsteht-im-handler.md)); für ihn
ist die Ausstellung genau ein Schritt hinter genau einem Port.

Der Preis ist bewusst gewählt: der Adapter ist damit dicker als die anderen vier. Die Alternative
wäre, mehrere Domain-Ports in den Handler zu hängen — dann kennte der Fachablauf die Reihenfolge
von Zufall, Ablage und Signatur, also lauter Handwerk. Das wäre der schlechtere Tausch.

Ausgerechnet wird dabei nichts: den Ablauf beantwortet `TokenLifetime.expires_from`, die Felder
der Zeile das Aggregat. Der Adapter fragt beide und wickelt die Antworten auf Primitive ab.

## Was der Klartext nie berührt

Der Klartext des Refresh-Token geht vom Aussteller direkt in die `IssuedCredentials` und von dort
in die Antwort. Er kommt in der Domäne **nicht** vor: `RefreshToken.issue` bekommt nur den
`TokenHash`. Damit gibt es keinen Weg, auf dem er versehentlich in eine abgelegte Zeile geriete.
