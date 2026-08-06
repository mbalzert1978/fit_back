"""Domain-Unit-Tests des Identity-Context.

Eigene Testebene neben den Use-Case-Specs (docs/milestones/02-test-pyramide.md,
unterste Ebene; BACKEND.md Abschnitt 9): je Aggregat, Value Object und Union,
ohne Mocking. Diese Tests greifen bewusst direkt auf die Domaene zu - sie sind
kein Slice-Spec und laufen deshalb nicht ueber die Test-API.
"""
