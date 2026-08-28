"""Was im ausgestellten Access-Token wirklich steht.

Die Specs des Slice fahren den Fake, und der Vertrag des Frontends prueft
`accessToken` nur auf seinen Typ - beide koennten gruen bleiben, waehrend das
echte Token einen falschen Nutzer nennt, nie ablaeuft oder mit einem fremden
Geheimnis signiert waere. Deshalb wird hier das Token selbst aufgemacht.
"""

import jwt
import pytest

from src.contexts.identity.infrastructure.tokens.jwt_access_tokens import (
    ALGORITHM,
    JwtAccessTokens,
)

GEHEIMNIS = "ein-geheimnis-mit-mindestens-32-zeichen"
AUSGESTELLT_AM = 1700000000
"""Unix-Sekunden, 2023-11-14 - bewusst in der Vergangenheit: ein `iat` in der
Zukunft lehnt `pyjwt` als "not yet valid" ab, und das waere hier nicht der Punkt.
"""

GELTUNGSDAUER = 900
"""Sekunden - hier eine Vorgabe des Tests, keine Konstante der Produktion."""


def _token(user_id: str = "01920000-0000-7000-8000-000000000001") -> str:
    return JwtAccessTokens(GEHEIMNIS).sign(user_id, AUSGESTELLT_AM, AUSGESTELLT_AM + GELTUNGSDAUER)


def test_das_token_nennt_den_nutzer_und_seinen_ablauf() -> None:
    """`sub`, `iat`, `exp` - registrierte Claims, damit jeder Pruefer sie kennt."""
    claims = jwt.decode(_token(), GEHEIMNIS, algorithms=[ALGORITHM], options={"verify_exp": False})

    assert claims["sub"] == "01920000-0000-7000-8000-000000000001"
    assert claims["iat"] == AUSGESTELLT_AM
    assert claims["exp"] - claims["iat"] == GELTUNGSDAUER


def test_ein_fremdes_geheimnis_oeffnet_das_token_nicht() -> None:
    """Ohne diese Zusage waere die Signatur Zierde."""
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(
            _token(),
            "ein-anderes-geheimnis-lang-genug-32",
            algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )


def test_das_abgelaufene_token_wird_abgelehnt() -> None:
    """Der Ablauf gilt, weil er als `exp` steht - nicht, weil jemand daran denkt."""
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(_token(), GEHEIMNIS, algorithms=[ALGORITHM])
