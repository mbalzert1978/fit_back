"""Das veroeffentlichte Vokabular des Identity-Context.

Der einzige Teil dieses Context, den ein anderer importieren darf. `domain/` und
`infrastructure/` sind fuer Fremde gesperrt (`forbidden`-Contract in setup.cfg),
`application/` gehoert dem Slice - was hier steht, ist bewusst nach aussen
gegeben und aendert sich nicht ohne Ruecksicht auf die Konsumenten.

Deshalb haengt dieses Paket an **nichts** ausser der stdlib und dem Shared
Kernel: ein Konsument, der ein Ereignis dieses Context lesen will, soll dafuer
nicht dessen halbe Domaene mitziehen muessen.
"""

from src.contexts.identity.contracts.user_registered import UserRegistered

__all__ = ["UserRegistered"]
