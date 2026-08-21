"""A provider-verification run, assembled fluently.

This is the mechanics no test wants to read: the app under `uvicorn` in a
thread, the `pact-python` verifier, and the bridge that pulls state handlers
from Pact's own thread back onto the test's event loop. A test only states
**what** gets verified:

    await (
        ProviderVerification.for_provider("nutritrack-identity", identity_pact)
        .only_paths(PurePosixPath("/api/v1/identity/register"))
        .with_state("Konto existiert", setup=account.create, teardown=account.remove)
        .verify(app, pact_store)
    )

Neither here nor in the test does a file get opened: `conftest.py` hands in
the finished `Pact` and the `Store` the verifier needs to read - it is the
only place that imports `json` and touches the filesystem.

Reusable for the remaining five contracts once their contexts are built - each
gets its own run under its own provider name.
"""

import asyncio
import contextlib
import threading
from enum import Enum
from collections.abc import AsyncGenerator, Awaitable, Callable, Collection, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Self, assert_never, final

import uvicorn
from fastapi import FastAPI
from pact.verifier import Verifier

__all__ = ["Interaction", "Pact", "ProviderVerification", "State", "Store"]

type Hook = Callable[[], Awaitable[None]]

type Store = Callable[[Mapping[str, object]], Path]
"""Writes the pact to replay and names the file.

`pact-python` reads its source from the filesystem - the reduced pact has to
land somewhere. Where is up to the test's fixture, not this toolkit.
"""


class Phase(str, Enum):
    """The two halves Pact calls a state handler with."""

    setup = "setup"
    teardown = "teardown"


_START_FRIST = 30.0
"""Seconds the app has to start up before the run aborts."""

_STOPP_FRIST = 10.0
"""Seconds the uvicorn thread has to shut down.

If it runs out the test proceeds anyway: the thread is a daemon and dies with
the process. Waiting here only frees the port before the next run needs it.
"""


def _as[T](value: object, expected: type[T], where: str) -> T:
    """Take a value out of a pact as the type it must be.

    Anything from a JSON file starts out as plain `object`. Instead of blurring
    that with `Any`, this surfaces a pact built differently than assumed - with
    the field name in the error text.
    """
    if not isinstance(value, expected):
        msg = f"The pact carries no {expected.__name__} under {where}, but {type(value).__name__}."
        raise TypeError(msg)
    return value


@final
@dataclass(frozen=True, slots=True)
class Interaction:
    """One interaction of the pact - it knows itself which endpoint it targets.

    `path` is a `PurePosixPath`, not a string or a URL type. Not a string,
    because that type compares `/api/v1/x` and `/api/v1//x` as equal, where a
    string would see two different things. `PurePosixPath` instead of `Path`,
    so Windows backslash semantics can't slip in. And not a URL type, because
    the pact holds exactly what the field name says - a path. Scheme, host and
    query don't exist there; a URL type would model three fields that stay
    empty and raise the question of which host to compare against.

    `raw` stays attached because a replayed pact has to be a valid pact file
    again: whatever the builder doesn't read, it hands back unchanged.
    """

    path: PurePosixPath
    raw: Mapping[str, object]

    @classmethod
    def from_raw(cls, raw: Mapping[str, object]) -> "Interaction":
        request = _as(raw["request"], Mapping, "request")
        return cls(PurePosixPath(_as(request["path"], str, "request.path")), raw)

    def targets(self, paths: Collection[PurePosixPath]) -> bool:
        return self.path in paths


@final
@dataclass(frozen=True, slots=True)
class Pact:
    """A pact file, split into its interactions and everything else."""

    head: Mapping[str, object]
    interactions: tuple[Interaction, ...]

    @classmethod
    def from_raw(cls, raw: Mapping[str, object]) -> "Pact":
        """Interpret the parsed contents of a pact file.

        The single place that knows a pact's shape - from here on everything
        hangs off names instead of key chains. The file itself is read in
        `conftest.py`; what arrives here is already parsed.
        """
        return cls(
            head={name: value for name, value in raw.items() if name != "interactions"},
            interactions=tuple(
                map(Interaction.from_raw, _as(raw["interactions"], list, "interactions"))
            ),
        )

    def only_on(self, paths: Collection[PurePosixPath]) -> "Pact":
        return Pact(self.head, tuple(i for i in self.interactions if i.targets(paths)))

    @property
    def content(self) -> Mapping[str, object]:
        return {**self.head, "interactions": [i.raw for i in self.interactions]}


@final
@dataclass(frozen=True, slots=True)
class State:
    """A provider state: what sets it up, and what tears it back down.

    Kept as two separate halves because Pact calls them separately, and the
    teardown is the more important part: it decides whether two interactions
    on the same state interfere with each other.
    """

    name: str
    setup: Hook
    teardown: Hook

    def pick(self, phase: Phase) -> Hook:
        match phase:
            case Phase.setup:
                return self.setup
            case Phase.teardown:
                return self.teardown
            case _:
                assert_never(phase)


@final
class ProviderVerification:
    """A verification run, built up step by step."""

    def __init__(self, provider: str, pact: Pact) -> None:
        self._provider = provider
        self._to_replay = pact
        self._states: list[State] = []

    @classmethod
    def for_provider(cls, provider: str, pact: Pact) -> Self:
        """Start a run of this provider against this pact.

        Both together, because a run without a pact is nothing that should be
        startable by accident.
        """
        return cls(provider, pact)

    def only_paths(self, *paths: PurePosixPath) -> Self:
        """Restrict the run to the interactions of these endpoints.

        What gets replayed is then a reduced pact - a copy carrying only the
        chosen interactions. The stakeholder's file stays untouched, and the
        exclusion hangs off what the ticket means: the endpoint. Not off
        description text the consumer can reword at any time.
        """
        chosen = self._to_replay.only_on(paths)
        if not chosen.interactions:
            msg = f"The pact has no interaction on {[str(p) for p in paths]}."
            raise LookupError(msg)
        self._to_replay = chosen
        return self

    def with_state(self, name: str, *, setup: Hook, teardown: Hook) -> Self:
        self._states.append(State(name, setup, teardown))
        return self

    async def verify(self, asgi_app: FastAPI, store: Store) -> None:
        """Boot the app, replay the pact against it, tear down again.

        If the run fails, `pact-python` raises - that's the test result.
        """
        loop = asyncio.get_running_loop()
        source = store(self._to_replay.content)

        async with _running_app(asgi_app) as url:
            verifier = (
                Verifier(self._provider, host="127.0.0.1")
                .add_transport(url=url)
                .add_source(source)
                .state_handler({s.name: _handler(s, loop) for s in self._states}, teardown=True)
                # An empty pact is a failure, not a green run.
                .set_error_on_empty_pact(enabled=True)
            )
            # In a thread, so the test's loop stays free for the state handlers.
            await asyncio.to_thread(verifier.verify)


def _handler(state: State, loop: asyncio.AbstractEventLoop) -> Callable[..., None]:
    """Build the synchronous handler `pact-python` expects from a `State`.

    Pact calls the state handlers from its own small HTTP server's thread. The
    test's database engine belongs to that test's event loop though; used from
    a foreign thread, asyncpg falls over. The detour through
    `run_coroutine_threadsafe` hands the work back there - possible because
    `verify()` runs the verifier itself in a thread, leaving the test's
    loop free.
    """

    # `action` is **not** free to rename: `pact-python` inspects the handler's
    # signature and only passes the arguments whose parameters are named
    # exactly `state`, `action`, or `parameters` (`Verifier.state_handler` ->
    # `apply_args`). A different name here leaves the handler called with no
    # argument, and the run aborts with "state change handlers has failed" -
    # measured. The name belongs to Pact, not this repo's glossary.
    def handler(action: Phase) -> None:
        asyncio.run_coroutine_threadsafe(state.pick(action)(), loop).result()

    return handler


@contextlib.asynccontextmanager
async def _running_app(asgi_app: FastAPI) -> AsyncGenerator[str]:
    # Port 0: the OS picks a free one and reports it back via the socket. A
    # self-chosen port would be free for others between the pick and `bind()`.
    server = uvicorn.Server(uvicorn.Config(asgi_app, host="127.0.0.1", port=0, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        async with asyncio.timeout(_START_FRIST):
            while not server.started:
                # Wait on `is_alive()` too, not just `started`: if startup
                # aborts - missing config, say - uvicorn never sets `started`,
                # and waiting alone would hide the reason.
                if not thread.is_alive():
                    msg = "The app aborted on startup - see uvicorn's output."
                    raise RuntimeError(msg)
                await asyncio.sleep(0.05)
        yield f"http://127.0.0.1:{_bound_port(server)}"
    finally:
        server.should_exit = True
        await asyncio.to_thread(thread.join, _STOPP_FRIST)


def _bound_port(server: uvicorn.Server) -> int:
    return server.servers[0].sockets[0].getsockname()[1]
