---
schema_version: 1
name: subprocess-python-literal-vs-sys-executable
description: subprocess.run(["python", ...]) loest sich ueber PATH auf, nicht zum aktiven uv-Venv - fuer Tests/Fixtures, die den eigenen Interpreter erneut aufrufen, muss sys.executable verwendet werden
type: project
frequency: 1
last_triggered: 2026-08-06
decay_eligible: false
---

`subprocess.run(["python", ...])` startet, welches `python` gerade auf `PATH` steht - das kann ein
System-Python ohne die Projekt-Dependencies sein, selbst wenn der aufrufende Prozess selbst im
uv-Venv laeuft. Fuer jeden Subprocess-Aufruf, der den *gleichen* Interpreter (inkl. installierter
Pakete) erneut aufrufen soll, muss `sys.executable` statt des String-Literals `"python"` verwendet
werden.

**Why:** `tests/conftest.py`s `alembic_migrations`-Fixture rief `subprocess.run(["python", "-m",
"alembic", "upgrade", "heads"], ...)` auf. Lokal unter Windows loeste sich `"python"` zu einem
System-Python auf (`AppData\Local\Python\bin\python.exe` bzw. der WindowsApps-Stub), der kein
Alembic installiert hatte - `No module named alembic.__main__`. `uv run python -m alembic --help`
im selben Terminal funktionierte einwandfrei, weil `uv run` explizit den Venv-Interpreter waehlt;
das Fixture selbst tat das nicht.

**How to apply:** Bei jedem neuen Subprocess-Aufruf in Tests/Fixtures/Skripten, der ein
Python-Modul im *aktuell aktiven* Interpreter ausfuehren soll: `sys.executable` verwenden, nie ein
hartcodiertes `"python"`- oder `"python3"`-Literal.
