# Die Fehlernutzlast als typisierter Fall wird verbindliche Regel

**Datum:** 2026-08-07, 06:46

## Problem

Die Entscheidung von 06:34
([`…-0634-fehlercodes-statt-prosa-aus-dem-slice.md`](2026-08-07-0634-fehlercodes-statt-prosa-aus-dem-slice.md))
haelt fest, dass der Slice Fehlercodes statt Prosa zurueckgibt. Sie galt aber nur fuer den Umbau in
Ticket 0008. Solange die Regel nicht in `.rules/python/` steht, baut jeder neue Slice weiter
`Result[..., str]` mit fertigem deutschem Satz — und der Umbau in 0008 wird mit jedem
zwischenzeitlich gebauten Use Case teurer.

Erschwerend: `.rules/python/python-error-handling.md` **empfahl** die alte Form ausdruecklich.
`Result[Mac, str]` stand dort als Vorbild fuer Value-Object-Parsing, und das Do-Beispiel gab
`Err(f"invalid mac address: {raw}")` zurueck. Wer regelkonform arbeitete, baute genau das, was jetzt
umgebaut werden muss.

## Entscheidung

**Die Form wird Regel, nicht Ticket-Inhalt.** `.rules/python/python-error-handling.md` bekommt den
Abschnitt „Die Fehlernutzlast ist ein typisierter Fall, nie ein fertiger Satz": jeder Fehlschlag,
dessen Formulierung je einen Menschen erreichen kann, ist ein eigener
`@final @dataclass(frozen=True, slots=True)`-Fall mit typisierter Nutzlast in einer geschlossenen
Union. Ein `str` als `E` ist dort ein Regelverstoss.

Abgegrenzt bleibt die **Diagnose**: die `OSError`-Meldung im IO-Adapter, Log-Text, der Grund eines
Infrastruktur-Fehlschlags duerfen weiter `str` sein. Faustregel in der Regel selbst: erreicht die
Formulierung je eine Antwort an einen Aufrufer, ist sie ein typisierter Fall.

Die beiden Beispiele, die der neuen Regel widersprachen, sind mitgezogen
(`Result[Mac, MacError]` statt `Result[Mac, str]`), und der Index in `.rules/python/README.md`
nennt das Thema jetzt.

## Folgen

- **Der Bestand verletzt die Regel ab sofort an 7 Stellen** — die `parse`-Factories in
  `shared_kernel/not_empty_string.py` und den sechs Identity-Value-Objects. Das ist gewollt und
  exakt der Umfang von Ticket 0008; es ist damit kein „neuer" Befund mehr, sondern eine bekannte,
  terminierte Schuld.
- `review-against-rules` prueft ab jetzt gegen die geschaerfte Datei und meldet neue Verstoesse,
  bevor sie in `main` landen.
- Neue Slices bauen die Form von Anfang an. Die Referenz im Repo ist
  `contexts/identity/domain/email_errors.py`.
