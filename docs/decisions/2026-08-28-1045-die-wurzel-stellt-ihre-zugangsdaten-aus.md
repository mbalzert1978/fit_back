# Die Wurzel stellt ihre Zugangsdaten aus — der Handler fragt, statt herauszunehmen

## Was entschieden wurde

`User.issue_credentials(secrets, access_tokens, access_lifetime, refresh_lifetime)` ist die eine
Stelle, an der Zugangsdaten entstehen. Die Wurzel stellt den Refresh-Token aus, lässt den
Access-Token signieren und paart beide mit ihrer Geltungsdauer. Sie gibt zurück, was abzulegen ist,
und legt es nicht selbst ab.

| neu | was es ist |
|-----|------------|
| `User.issue_credentials` | die Operation — Method Injection für beide Mitspieler |
| `CredentialIssuance` (in `entities/user.py`) | das abzulegende `RefreshToken` und die fertigen `IssuedCredentials` |
| `domain/value_objects/credentials.py` | `Grant` und `IssuedCredentials`, zurück in der Domäne |

Geändert: `RefreshTokenIssuance` trägt jetzt `refresh_token` und `grant` statt `token` und
`plaintext` — die Paarung Klartext↔Geltungsdauer entsteht in `RefreshToken.issue`, wo die Dauer
bekannt ist. `Grant` trägt die Konstruktor-Sperre (`hydrate`), weil es einen Rohwert hält.

Gelöscht: `application/register_user/credentials.py`.

Unangetastet: die HTTP-Antwort, die public Naht, die Adapter, der Fake, sämtliche Specs, das
Datenbankschema — **keine Migration**.

## Warum die alte Form falsch war

Der Handler holte sich `user.id` und `user.registered_at` aus der Wurzel heraus und trug sie an drei
Stellen weiter — in `RefreshToken.issue` und zweimal in die Signatur-Anfrage. Das ist Feature Envy:
eine Methode, die mehr mit fremden Daten arbeitet als mit eigenen. Die Wurzel war ein Behälter, aus
dem man Werte entnimmt, statt ein Aggregat, das man fragt — genau das anämische Modell, das dieses
Repo ausschließt (BACKEND.md Abschnitt 0, Punkt 10).

Jetzt steht im Handler kein einziger Zugriff auf ein Feld des `User` mehr. Er fragt, und die Wurzel
antwortet mit dem fertigen Ergebnis.

## Was das an der Entscheidung von 09:30 korrigiert

[Das Aggregat zieht sein Geheimnis selbst](2026-08-28-0930-das-aggregat-zieht-sein-geheimnis-selbst.md)
schob `IssuedCredentials` in den Slice, mit der Begründung, der Typ trage keine Invariante und sei
nur ein Ergebnis auf dem Weg nach draußen.

Das war unter den damaligen Verhältnissen richtig: den Typ setzte der Handler aus Einzelteilen
zusammen, und niemand in der Domäne kannte ihn. Mit `User.issue_credentials` ist er der
**Rückgabewert einer Aggregat-Operation** — und damit Domänen-Vokabular, so wie
`RefreshTokenIssuance` es ist. Er wandert zurück nach `domain/value_objects/`.

Der Ort folgt hier nicht dem Typ, sondern seinem Erzeuger. Solange ein Adapter ihn zusammensetzte,
gehörte er nach außen; sobald die Wurzel ihn ausstellt, nach innen.

## Was die Wurzel nicht tut

**Ablegen.** `issue_credentials` gibt das `RefreshToken` heraus, der Handler ruft `store`. Ein
Aggregat, das sich selbst speichert, ist ein Active Record: es zöge die Ablage in die Domäne und
machte jeden Test der Ausstellung von einer Transaktion abhängig.

**Das breite Port halten.** Die Wurzel bekommt `TokenSecrets`, nicht `RefreshTokens` — also
`mint()` ohne `store()`. Der Handler reicht dasselbe Objekt herein; welche Hälfte davon sichtbar
ist, entscheidet der Parametertyp. Interface Segregation an der Stelle, an der sie etwas
verhindert.

**Die Mitspieler behalten.** Beide Ports kommen in die **Methode**, nie in ein Feld. Ein Aggregat
mit Mitspieler-Feldern ist keines mehr: es ließe sich nicht mehr aus der Ablage rekonstruieren,
ohne die halbe Infrastruktur mitzubringen.

## Was der Handler jetzt ist

Drei Zeilen: fragen, ablegen, einpacken. Kein Zugriff auf ein Feld des `User`, kein Geheimnis, kein
Zeitpunkt, keine Rechnung. Der Weg dahin führte über zwei Zwischenstände an einem Tag —
[0807](2026-08-28-0807-das-aggregat-stellt-sich-selbst-aus.md) gab dem Aggregat die Paarung,
[0930](2026-08-28-0930-das-aggregat-zieht-sein-geheimnis-selbst.md) den Zufall und dem Handler den
Ablauf, und erst hier verschwindet der letzte Griff in fremde Felder.
