# Entitäten wechseln ihren Zustand als neue Instanz

## Was entschieden wurde

Eine Entität in diesem Repo bleibt eine gewöhnliche Klasse mit identitätsbasierter Gleichheit —
kein `frozen`-Dataclass, denn Gleichheit über alle Felder wäre bei einer Entität schlicht falsch.

Ein Zustandswechsel wird trotzdem **nicht** durch Mutation ausgedrückt. Die Methode gibt eine neue
Instanz mit derselben Identität und den neuen Werten zurück.

## Warum

Ein Aggregat, das sich unter dem Aufrufer verändert, macht jede Zeile davor fragwürdig: hielt sie
denselben Zustand? Wer stattdessen eine neue Instanz zurückgibt, macht den Wechsel im Ablauf
sichtbar — der alte Stand bleibt lesbar, der neue steht in einer neuen Bindung.

Das deckt sich mit `.rules/common/coding-style.md` („Keine Mutation"), ohne die Entität zu einem
Value Object zu machen. DDD verlangt für eine Entität Identität über die Zeit, nicht
Veränderlichkeit im Speicher.

## Was heute gilt

`RefreshToken` hat noch **kein** zustandsänderndes Verhalten. Diese Entscheidung baut deshalb
nichts, sie legt die Form fest, in der Widerruf und Rotation mit
[#53](https://github.com/mbalzert1978/fit_back/issues/53) entstehen. Wie die Methoden dort heißen
und was sie tragen, entscheidet dieses Ticket — hier steht nur, dass sie eine neue Instanz
zurückgeben und nicht mutieren.
