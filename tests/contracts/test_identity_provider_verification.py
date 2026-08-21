"""Provider verification against the frontend's identity pact (ticket #94).

The pact under `contracts/pacts/identity/` is the HTTP boundary's specification
(`docs/decisions/2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md`).

**The run against it is red as expected**, for as long as
`POST /api/v1/identity/register` doesn't satisfy it. A pact from the consumer
is a specification, not proof - red here means "not built yet", not "tested
wrong". It goes green with the ticket that builds the endpoint.

Because a red run can't prove anything, the **mechanics** also run against a
second, small pact whose consumer is this repo itself: same path, same wiring,
but green. It proves what the ticket requires - two interactions on the same
state don't interfere with each other.

Only the five `register` interactions run; `login`, `refresh`, `logout`, and
`me` aren't built yet and stay excluded via `REGISTER_PATH` until their
respective ticket lands. The mechanics behind this live in
`provider_verification.py`; `conftest.py` hands in both pacts and the `Store` -
this module opens no file itself.
"""

from pathlib import PurePosixPath

import pytest

from src.main import app
from tests.contracts.account import Account
from tests.contracts.conftest import EMAIL, PASSWORD
from tests.contracts.provider_verification import Pact, ProviderVerification, Store

PROVIDER = "nutritrack-identity"

REGISTER_PATH = PurePosixPath("/api/v1/identity/register")
"""The one endpoint that's built today - and so the only one that runs.

Another one costs a line here plus the states carrying its interactions;
which interactions those are, the builder reads off the pact.
"""

# The states name their account in plain text instead of carrying it as a V3
# `parameters` - hence the literal text here. Both values come from
# `conftest.py`, since the `account` fixture there is built from the same.
NO_ACCOUNT = f"Keine Registrierung mit {EMAIL} vorhanden"
ACCOUNT_EXISTS = f"Nutzer {EMAIL} existiert mit Passwort {PASSWORD}"

pytestmark = pytest.mark.asyncio


async def test_registration_fulfils_the_identity_contract(
    account: Account,
    identity_pact: Pact,
    pact_store: Store,
) -> None:
    """Replay the five register interactions against the running app."""
    await (
        ProviderVerification.for_provider(PROVIDER, identity_pact)
        .only_paths(REGISTER_PATH)
        .with_state(NO_ACCOUNT, setup=account.remove, teardown=account.remove)
        .with_state(ACCOUNT_EXISTS, setup=account.create, teardown=account.remove)
        .verify(app, pact_store)
    )


async def test_two_interactions_sharing_a_state_do_not_interfere(
    account: Account,
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
        .with_state(ACCOUNT_EXISTS, setup=account.create, teardown=account.remove)
        .verify(app, pact_store)
    )
