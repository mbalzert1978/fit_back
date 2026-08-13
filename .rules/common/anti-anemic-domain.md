# Kein blutarmes Domänenmodell

## Grundsatz (KRITISCH)

Objekte erledigen ihre Arbeit selbst. Handler orchestrieren, sie führen nicht aus.

Eine **blutarme Domäne** behandelt Objekte als passive Datenbehälter — der Handler fragt Ports ab,
liest rohe Felder aus und erledigt die Domänenlogik selbst.
Eine **reiche Domäne** legt die Logik dorthin, wo die Daten liegen — das Objekt ruft den Port und
liefert ein aussagekräftiges Ergebnis.

```text
// Pseudocode
FALSCH:  wenn !port.IstBereit(objekt) → zurück; wenn !port.IstBereit(objekt.Geschwister) → zurück; ergebnis = Typ.Bilde(objekt.a, objekt.b)
RICHTIG: ergebnis = objekt.LöseAuf(port)   // das Objekt entscheidet, was „bereit" heißt und wie es sich bildet
```

## Verantwortung eines Handlers

Ein Handler darf nur:

- eine Anfrage entgegennehmen
- Abhängigkeiten (Ports) an Domänenobjekte durchreichen
- das Ergebnis festschreiben (in den Speicher schreiben, Ereignis veröffentlichen, zurückgeben)

Ein Handler darf nie:

- Ports wiederholt aufrufen, um Bedingungen zu rekonstruieren, die die Domäne bereits kennt
- rohe Felder auslesen, um sie in statische Factory-Aufrufe zu füttern
- „Ist dieses Objekt bereit?" in `if`-Ketten kodieren
- Port-Aufrufe wiederholen, die Domänen-Invarianten duplizieren

## Muster: das Objekt ruft den Port

`objekt.Operation(port, ct)` ist `port.Operation(objekt, ct)` vorzuziehen.

Das Objekt besitzt die Invariante. Es weiß, welche Port-Aufrufe es braucht und was deren Ergebnisse
bedeuten. Der Port ist eine injizierte Abhängigkeit — eine Naht, kein Entscheider.

```csharp
// RICHTIG — das Objekt treibt, der Port ist die Naht
if (await request.Path.FormGroupAsync(grouping, ct) is not { } group)
    return new GroupingResult.Pending();

await group.MarkMembersGroupedAsync(grouping, ct);

// FALSCH — der Handler treibt, das Objekt ist passive Daten
if (!await grouping.IsDownloadedAsync(request.Path, ct)) return Pending();
if (!await grouping.IsDownloadedAsync(candidate.Sibling.Value, ct)) return Pending();
FileGroup group = FileGroup.Form(candidate.Stem, candidate.Jpl, candidate.Pdf);
await grouping.MarkGroupedAsync(candidate.Jpl.Value, candidate.Stem.Value, ct);
await grouping.MarkGroupedAsync(candidate.Pdf.Value, candidate.Stem.Value, ct);
```

## Was die Domäne besitzt

Domänenobjekte besitzen:

- die Entscheidung, ob eine Operation möglich ist
- wie sie sich bilden oder in einen anderen Zustand übergehen
- die Benennung ihrer eigenen Wertbegriffe (Stamm, Geschwister, Schlüssel)
- die Iteration über ihre eigenen Mitglieder

Domänenobjekte besitzen nicht:

- IO (der Port wird hineingereicht, nicht konstruiert)
- das Veröffentlichen von Ereignissen (der Handler veröffentlicht, was die Domäne erzeugt hat)
- Fehleraufbereitung oder Protokollierung

## Checkliste

Bevor ein Handler als fertig gilt:

- [ ] Der Handler hat keine mehrstufigen Port-Abfragen, die Domänenzustand rekonstruieren
- [ ] Statische Factory-Aufrufe (`Typ.Bilde(a, b, c)`) stehen im Domänenobjekt, nicht im Handler
- [ ] Operationen über Mitglieder sind ein Aufruf auf dem Aggregat, nicht N Aufrufe im Handler
- [ ] Der Handler-Rumpf passt in etwa 10 Zeilen (nur Orchestrierung)
- [ ] Jede Verzweigung über Domänenzustand steht in Domänenmethoden, nicht in `if`-Ketten im Handler
