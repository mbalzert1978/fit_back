# Zehn Widersprüche in `.rules/` aufgelöst

Eine Analyse aller 21 Dateien unter [`.rules/`](../../.rules/) gegeneinander hat zehn
Widersprüche gefunden, die die dokumentierte Vorrang-Reihenfolge
([`.rules/python/README.md`](../../.rules/python/README.md)) **nicht** auflöst — überwiegend
zwischen zwei Dateien derselben Ebene, wo keine die speziellere ist. Alle zehn sind hier
entschieden und in den Regel-Dateien nachgezogen. Was sich sauber über den Vorrang auflöst
(generisches Repository, Handler-Länge, „Fehler auf jeder Ebene behandeln", API-Antwort-Hülle),
blieb unangetastet.

## Was entschieden wurde

1. **`domain/` darf den Shared Kernel nutzen.** Die Schicht war auf „nur stdlib" festgelegt und
   zugleich verpflichtet, `Result[T, E]` und `ResultRule` zu sprechen — beides liegt in
   `shared_kernel/`. Die Abhängigkeitsspalte lautet jetzt „nur stdlib + `shared_kernel` (der selbst
   nur stdlib nutzt)". Ausgeschlossen ist damit die Lesart, die Domäne müsse `Result` selbst
   nachbauen.
2. **Die public Naht ist von der `Result`-Pflicht ausgenommen.** „Jeder binäre Ausgang ist ein
   `Result[T, E]`" galt wörtlich auch für den Naht-Vertrag, den `python-feature-slices.md` als
   eigene Tagged Union vorschreibt. Die Ausnahme steht jetzt in
   `python-error-handling.md` — analog zur bereits sauber notierten Aggregatwurzel-Ausnahme.
3. **Der Abschlusszweig eines `match` ist `assert_never`, überall.**
   `python-control-flow.md` schrieb `raise AssertionError(...)` vor, was
   `python-error-handling.md` ausdrücklich als unzureichend führt. Die Exhaustivitätsregel steht
   fachlich nur noch an einer Stelle; `control-flow` verweist dorthin.
4. **Guards sichern Programmierfehler, nicht Eingaben.** `python-null-safety.md` grenzt jetzt ab:
   ein werfender Guard sichert eine interne public Grenze, seine Meldung ist Diagnose. Werte über
   die Systemgrenze laufen über die Collect-all-`Rule` im Validierungs-Behavior und enden als
   typisierter Fall — nie als Exception, nie als fertiger Satz.
5. **Der Code illustriert die Regel, er ersetzt sie nicht.** Der Satz „im Zweifel gilt der Code als
   Vorbild, nicht die Prosa" gab der Referenzimplementierung einen Vorrang, den die
   Konfliktauflösung nicht kennt — bei Drift hätte der Code jede Regel still ausgehebelt. Jetzt
   gilt bei Abweichung die Regel-Datei; der Code wird nachgezogen oder die Regel bewusst hier
   geändert.
6. **Kein Logger im fachlichen Typ, auch nicht im Wiring-Beispiel.** Das Do-Beispiel in
   `python-factories.md` injizierte einen Logger in einen Handler — das Don't von
   `python-dependencies.md`. Es zeigt jetzt die Decorator-Verdrahtung.
7. **Kein `str` als `E`.** Der Kommentar `Result[ScopeId, str]` widersprach der Regel, dass die
   Fehlernutzlast ein typisierter Fall ist; er lautet jetzt `Result[ScopeId, ScopeIdError]`.
8. **Der `_`-Präfix ist nicht Test-Modulen vorbehalten.** Der Satz war wörtlich das Gegenteil des
   Gemeinten und widersprach dem Do-Beispiel zwölf Zeilen darüber. Vorbehalten ist Test-Modulen
   das *Unterlaufen* der Grenze.
9. **Die Walrus-Pflicht gilt auch für das `match`-Subjekt.** Hier wurde bewusst **nicht** die
   Walrus-Regel eingeschränkt: sie bleibt ausnahmslos. Stattdessen bindet
   `python-error-handling.md` den Namen jetzt im Subjekt (`match outcome := await …:`) statt in
   einer freistehenden Zuweisung davor.
10. **Logging ist die Ausnahme zur f-String-Regel.** `logger.<level>("… %s …", wert)` ist keine
    `%`-Formatierung im Sinn der Regel, sondern die von ruff (`G004`) verlangte Form. Damit sind
    die Do-Beispiele in `python-null-safety.md` und `python-dependencies.md` gedeckt.

## Offene Folgearbeit

- `src/api/identity/register_user_router.py:92` bindet `outcome` noch freistehend vor dem `match`
  und weicht damit nach Entscheidung 9 von der Regel ab — nachzuziehen (Regel 5: der Code folgt).
- Die Abhängigkeitsspalte von `application/` nennt weiterhin ein „gemeinsames `common`-Paket",
  während im Repo `shared_kernel` liegt und kein `common` existiert (ebenso der Hinweis zu
  Ordnernamen in `python-feature-slices.md`). Das ist Doku-Drift, kein Widerspruch zwischen zwei
  Regeln, und wurde deshalb hier nicht mitentschieden.
