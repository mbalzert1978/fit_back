# Gemeinsame Muster

## Vorhandenes vor Neuem

Vor einer neuen Implementierung:

1. Nach erprobten Grundgerüsten und Referenzimplementierungen suchen
2. Die Kandidaten bewerten — Sicherheit, Erweiterbarkeit, Passung zum Problem
3. Den besten Treffer als Fundament übernehmen
4. Innerhalb der erprobten Struktur weiterarbeiten

## Entwurfsmuster

### Repository

Datenzugriff hinter einer einheitlichen Schnittstelle kapseln:

- Standardoperationen festlegen: alle finden, nach Id finden, anlegen, ändern, löschen
- Die konkrete Implementierung kennt die Speicherdetails (Datenbank, API, Datei)
- Die Fachlogik hängt an der Abstraktion, nicht am Speichermechanismus
- Das macht den Austausch der Datenquelle einfach und den Test ohne echte Quelle möglich

### Format der API-Antwort

Für alle API-Antworten dieselbe Hülle verwenden:

- ein Feld für Erfolg bzw. Status
- die Nutzlast (bei Fehler leer)
- ein Feld für die Fehlermeldung (bei Erfolg leer)
- Metadaten bei seitenweisen Antworten (Gesamtzahl, Seite, Seitengröße)

### Anti-Corruption Layer (Adapter an der Grenze)

Ein Adapter, der einen internen Typ über eine Modulgrenze hinweg auf einen externen abbildet, ist
**keine** überflüssige Durchreiche — auch dann nicht, wenn die Signaturen gleich aussehen. Er
entkoppelt das interne Modell vom externen und ist genau das, was die Naht prüfbar hält.

- Eine Brücke, die ein internes Kommando oder einen internen Marker (Domänensprache) in ein externes
  Infrastruktur-Kommando übersetzt, ist eine bewusste Grenze, keine Identitätshülle. Getrennte
  interne und externe Markertypen sind der Zweck: die Domäne hängt nur am internen, deshalb kann ein
  Test an dieser Naht ein Double einsetzen, ohne die externe Infrastruktur anzufassen.
- Eine Domänenschicht (Entität, Handler, Speicher-Schnittstelle) bleibt bestehen, auch wenn sie noch
  kein Verhalten trägt — dokumentierte künftige Anwendungsfälle landen dort von selbst. Der Umweg
  DTO → Entität → DTO ist der bewusste Preis der Trennung.

Solche Schichten im Review **nicht** als „dünne Hülle", „Identitäts-Wrapper", „wertlose
Indirektion" oder „Durchreiche" anmerken und ihre Löschung vorschlagen — das koppelt Intern direkt
an Extern und nimmt die Test-Naht weg. Das ist ein wiederkehrendes Fehlurteil in Reviews.
