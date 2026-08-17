# Vertrag `UserRegistered`

Die Dateien unter [`examples/`](./examples/) sind der **veroeffentlichte Vertrag** dieses
Ereignisses — nicht Dokumentation daneben, sondern die Wahrheit, gegen die geprueft wird.

- Eine `.json`-Datei je Fall, benannt `<version>-<fall>.json` (z. B. `v1-vollstaendig.json`).
- Die Datei enthaelt genau die **Nutzlast** (`to_payload()`), nicht den Transport-Umschlag.
- **Bei einer Abweichung ist die Datei massgeblich, nicht der Produktionscode.**
  `src/contexts/identity/specs/contracts/test_user_registered_contract.py` misst das
  tatsaechlich emittierte Ereignis dagegen — Feldmenge **identisch**, nicht nur Teilmenge.
- Ein Feld darf **additiv** dazukommen: neue Datei mit erhoehter `<version>`. Ein Feld
  umzubenennen oder zu entfernen ist ein **Bruch** und braucht ein eigenes Ticket, das die
  Konsumenten mitzieht.

Konsumenten (siehe [`docs/milestones/02-test-pyramide.md`](../../../../../../docs/milestones/02-test-pyramide.md),
Form B) importieren dieselben Dateien und belegen damit, dass ihr Handler mit jedem Beispiel
umgehen kann. Heute existiert noch keiner: Goals (M2) und Diary (M4) ziehen nach.
