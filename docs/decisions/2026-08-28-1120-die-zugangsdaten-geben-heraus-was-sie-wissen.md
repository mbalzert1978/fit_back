# Die Zugangsdaten geben heraus, was sie wissen — der Mapper greift nicht mehr hinein

## Was entschieden wurde

`Grant` und `IssuedCredentials` bekommen je einen `fold` — denselben Eliminator, den `Result` schon
trägt. Der Aufrufer sagt, was er bauen will, und bekommt die Werte gereicht.

```python
# vorher
return RegistrationAccepted(
    access_token=credentials.access.token,
    expires_in=credentials.access.lifetime.seconds,
    refresh_token=credentials.refresh.token,
    refresh_expires_in=credentials.refresh.lifetime.seconds,
)

# jetzt
return registration.credentials.fold(partial(_with_user, registration.user))
```

Geändert: `domain/value_objects/credentials.py` (zwei `fold`), der Response-Mapper (`_accepted`
schrumpft auf eine Zeile, `_with_user` setzt die Bestätigung zusammen).

Unangetastet: die HTTP-Antwort, jede Spec, das Datenbankschema.

## Warum die alte Form falsch war

**Vier Ketten durch zwei fremde Objekte.** `credentials.access.lifetime.seconds` ist drei Glieder
tief: der Mapper kannte `IssuedCredentials`, dessen `Grant` **und** dessen `TokenLifetime`. Ein
Message Chain in Reinform — und die klassische Gegenprobe fällt sofort durch: benennt `Grant` sein
Feld um, bricht der Mapper, obwohl er mit `Grant` nichts zu tun hat.

**Ask statt Tell.** Der Mapper nahm sich die Teile heraus und setzte sie selbst zusammen. Das ist
dieselbe Bewegung, die `_with_credentials` beim `User` machte
([1045](2026-08-28-1045-die-wurzel-stellt-ihre-zugangsdaten-aus.md)) — nur eine Schicht weiter
außen und deshalb beim ersten Durchgang übersehen.

## Warum `fold` und keine flachen Getter

Ein `Grant.seconds` hätte die Kette um ein Glied verkürzt und die Bewegung gelassen, wie sie war:
der Mapper fragt weiter ab. `fold` dreht die Richtung um. Der Aufrufer übergibt, was gebaut werden
soll; das Objekt ruft es mit seinen Werten auf und bleibt der einzige, der seine Felder kennt.

Es ist genau der Baustein, den das Repo für `Result` schon gewählt hat, und aus genau derselben
Begründung ([Result-fold als Eliminator](2026-08-26-1130-result-fold-als-eliminator.md)). Zwei
`fold` statt einem, weil es zwei Objekte sind: `IssuedCredentials.fold` reicht die eigenen zwei
Ausgaben weiter, ohne selbst in sie hineinzugreifen.

## Was bewusst so bleibt

Der Mapper liest weiterhin `user.email.value` und `user.registered_at.unix_seconds`. Das ist keine
Kette durch fremde Objekte, sondern das Auspacken eines Value Object an der äußeren Naht — genau
die Arbeit, für die ein Response-Mapper existiert
([`python-feature-slices.md`](../../.rules/python/python-feature-slices.md), „Primitive leben nur an
den äußeren Nähten"). Ein `User.fold` mit sechs Werten würde die Wurzel zum Antwortformat hin
formen, statt umgekehrt.
