# Gemeinsam genutzte Ressourcen kommen per Dependency Injection, nie aus einem Modul-Global

**Datum:** 2026-08-07, 07:50

## Problem

Die i18n-Ressourcen aus Ticket 0008 landeten zunaechst in einer Modulvariablen
(`src/api/i18n.py`), die eine Funktion `load_resources()` per `global` umbog. Dazu gehoerte ein
`AssertionError("Resources not loaded")` in `translate()`, der den unfertigen Zustand abfing.

Der Griff zum Global war nachvollziehbar: FastAPI-Exception-Handler bekommen nur `(request, exc)`
uebergeben, ueber die Signatur laesst sich dort nichts hereinreichen. Ein Modul-Global ist der
kuerzeste Weg an etwas heran, wenn die Signatur nichts hergibt.

Die Kosten trotzdem: verborgener Zustand, eine Initialisierungspruefung in jedem Aufruf, und Tests,
die sich gegenseitig den Zustand hinterlassen.

## Entscheidung

**Gemeinsam genutzte Ressourcen werden hereingereicht, nicht global gehalten.** Der Zusammenbau
besitzt die eine Instanz und legt sie dorthin, wo der Rand sie findet — genau so, wie dieses Repo
es mit der Datenbank-Engine bereits macht (`app.state.engine`, gelesen ueber `request.app.state`
in `src/middleware/idempotency.py`). Kein modulglobaler veraenderlicher Zustand, kein
`global`-Rebinding, keine Erzeugung beim Import oder bei der ersten Benutzung.

Der `AssertionError("Resources not loaded")` entfaellt ersatzlos: er pruefte einen Zustand, den es
ohne das Global nicht mehr geben kann.

Die praktische Probe: **jede Test-App muss ihre eigenen Ressourcen bekommen koennen**, ohne dass ein
Test den Zustand eines anderen sieht. Geht das nicht, ist die Injektion nicht echt.

## Warum nicht "eine Klasse draus machen"

Der uebliche Reflex bei `global` ist, eine Klasse zu fordern. Hier lag die Klasse (`_ResourcesCache`)
bereits vor und war trotzdem falsch verdrahtet — daneben stand eine modulglobale Instanz. Ein
Singleton mit `classmethod`-Zugriff waere derselbe verborgene Zustand im besseren Anzug. Der
tragfaehige Reflex lautet: **wo ein `global` steht, fehlt ein Besitzer** — und der Besitzer ist der
Zusammenbau, nicht eine neue Klasse.

## Folgen

- Gilt ueber i18n hinaus fuer jede kuenftige prozessweit geteilte Ressource am Rand (Caches,
  Clients, geladene Konfiguration).
- Ein Default-Parameter, der eine vergessene Uebergabe lautlos auffaengt (`language: str =
  DEFAULT_LANGUAGE`), steht damit ebenfalls unter Rechtfertigungszwang — er verdeckt genau den
  Fehler, den die Injektion sichtbar machen soll.
- Verwandt: `docs/reflections/exp_gestalt-beim-zusammenbau-nicht-im-startup.md` — dort geht es um
  den Zeitpunkt (Modulebene vs. Lifespan), hier um den Besitz.
