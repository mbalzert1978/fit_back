"""Provider verification against the frontend's identity pact (ticket #94).

The pact under `contracts/pacts/identity/` is the HTTP boundary's specification
(`docs/decisions/2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md`).

**The run is green since #95** built `POST /api/v1/identity/register` in the
shape the pact demands. It was red before that, and deliberately so: a pact
from the consumer is a specification, not proof - red meant "not built yet", not
"tested wrong". `register` grew from five to eight interactions when the
frontend's new pact landed; #95 was pulled along.

The **mechanics** also run against a second, small pact whose consumer is this
repo itself: same path, same wiring. It was the only green run while the
specification was still red, and it stays the proof of what the ticket requires -
two interactions on the same state don't interfere with each other.

Only the eight `register` interactions run; `password-reset`, `login`,
`refresh`, `logout`, and `me` aren't built yet and stay excluded via
`REGISTER_PATH` until their respective ticket lands (#52, #55 and their own).
The mechanics behind this live in `provider_verification.py`; `conftest.py`
hands in both pacts, the state helpers and the `Store` - this module opens no
file itself.
"""

from collections.abc import Awaitable, Callable
from pathlib import PurePosixPath

import pytest

from src.main import app
from tests.contracts.account import Account
from tests.contracts.conftest import EMAIL, PASSWORD
from tests.contracts.idempotency_key import IdempotencyKey
from tests.contracts.provider_verification import Pact, ProviderVerification, Store

PROVIDER = "nutritrack-identity"

REGISTER_PATH = PurePosixPath("/api/v1/identity/register")
"""The one endpoint that's built today - and so the only one that runs.

Its eight interactions; the pact's remaining eighteen sit on `password-reset`,
`me`, `refresh` and `logout` and are filtered out here.

Another one costs a line here plus the states carrying its interactions;
which interactions those are, the builder reads off the pact.
"""

# The states name their account in plain text instead of carrying it as a V3
# `parameters` - hence the literal text here. Both values come from
# `conftest.py`, since the `account` fixture there is built from the same.
NO_ACCOUNT = f"Keine Registrierung mit {EMAIL} vorhanden"
ACCOUNT_EXISTS = f"Nutzer {EMAIL} existiert mit Passwort {PASSWORD}"
KEY_TAKEN = "Unter dem Registrierungs-Schlüssel liegt schon ein Versuch mit anderem Rumpf"

pytestmark = pytest.mark.asyncio


def _both(
    first: Callable[[], Awaitable[None]], second: Callable[[], Awaitable[None]]
) -> Callable[[], Awaitable[None]]:
    """Run two hooks as one - Pact gives a state exactly one setup and one teardown.

    Needed since the pact reuses one `Idempotency-Key` across interactions: every
    state has to leave the key table empty, not just the account.
    """

    async def run() -> None:
        await first()
        await second()

    return run


async def test_registration_fulfils_the_identity_contract(
    account: Account,
    idempotency_key: IdempotencyKey,
    identity_pact: Pact,
    pact_store: Store,
) -> None:
    """Replay the eight register interactions against the running app."""
    await (
        ProviderVerification.for_provider(PROVIDER, identity_pact)
        .only_paths(REGISTER_PATH)
        .with_state(
            NO_ACCOUNT,
            setup=_both(account.remove, idempotency_key.clear),
            teardown=_both(account.remove, idempotency_key.clear),
        )
        .with_state(
            ACCOUNT_EXISTS,
            setup=_both(account.create, idempotency_key.clear),
            teardown=_both(account.remove, idempotency_key.clear),
        )
        .with_state(
            KEY_TAKEN,
            setup=_both(account.remove, idempotency_key.claim_for_another_body),
            teardown=_both(account.remove, idempotency_key.clear),
        )
        .verify(app, pact_store)
    )


async def test_two_interactions_sharing_a_state_do_not_interfere(
    account: Account,
    idempotency_key: IdempotencyKey,
    mechanik_pact: Pact,
    pact_store: Store,
) -> None:
    """Same account-creating state, twice in a row - both times through.

    If the first interaction's account were left standing, the second setup
    would run into `uq_users_email` and the run would go red.
    `Account.create()` deliberately doesn't clean up first, so this case
    actually occurs instead of being masked.
    """
    await (
        ProviderVerification.for_provider(PROVIDER, mechanik_pact)
        .with_state(
            ACCOUNT_EXISTS,
            setup=_both(account.create, idempotency_key.clear),
            teardown=_both(account.remove, idempotency_key.clear),
        )
        .verify(app, pact_store)
    )
