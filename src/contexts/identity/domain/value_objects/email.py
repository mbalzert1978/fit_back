"""Value Object Email - case-insensitiv normalisiert, aus einzelnen Regeln geprueft.

Bewusst **kein** Regex fuer die Gesamtadresse. Ein Adress-Regex behauptet mehr,
als ein Leser ihm ansehen kann: Label-Laenge, fuehrende/abschliessende
Bindestriche, Unterstriche in der Domain, IP-Literale, IPv6-Gruppenzahl - all das
steckt entweder unlesbar drin oder gar nicht. Stattdessen eine `chain(...)` aus
einzeln benannten Fail-fast-Regeln: jede beantwortet genau eine Frage, jede
meldet einen **eigenen typisierten Fehlerfall** statt einer Textzeile, und die
Testtabelle in `contexts/identity/specs/domain/test_email.py` prueft sie Fall
fuer Fall.
"""

from dataclasses import dataclass, field
from functools import partial
from ipaddress import ip_address
from typing import Final, Self, final

from src.contexts.identity.domain.email_errors import (
    EmailAddressLiteralInvalid,
    EmailDomainHasEmptyLabel,
    EmailDomainLabelHasEdgeHyphen,
    EmailDomainLabelHasInvalidCharacters,
    EmailDomainLabelTooLong,
    EmailDomainMissing,
    EmailDomainTooLong,
    EmailError,
    EmailHasWhitespace,
    EmailIsEmpty,
    EmailLocalPartHasInvalidCharacters,
    EmailLocalPartHasMisplacedDot,
    EmailLocalPartMissing,
    EmailLocalPartTooLong,
    EmailNeedsExactlyOneAtSign,
)
from src.contexts.identity.domain.ports.idn_encoder import IdnEncoder
from src.contexts.shared_kernel import ConstructionKey, Err, Ok, Result, deny_foreign_key
from src.contexts.shared_kernel.validation import ResultRule, chain

__all__ = ["MAX_DOMAIN_LENGTH", "MAX_LABEL_LENGTH", "MAX_LOCAL_LENGTH", "Email"]

MAX_LOCAL_LENGTH = 64
"""RFC 5321: der Local-Part fasst hoechstens 64 Zeichen."""

MAX_DOMAIN_LENGTH = 253
"""RFC 1035: der Domainname fasst hoechstens 253 Zeichen."""

MAX_LABEL_LENGTH = 63
"""RFC 1034: ein einzelnes Domain-Label fasst hoechstens 63 Zeichen."""

_LOCAL_SPECIALS = frozenset("!#$%&'*+-/=?^_`{|}~.")
"""Die von RFC 5322 im unquoted Local-Part erlaubten Sonderzeichen."""


def _split(candidate: str) -> tuple[str, str]:
    """Zerlege in Local-Part und Domain - erst aufrufen, wenn genau ein `@` sicher ist."""
    local, _, domain = candidate.partition("@")
    return local, domain


def has_no_whitespace(candidate: str) -> Result[str, EmailError]:
    r"""Kein Leerraum - irgendwo in der Adresse.

    Laeuft **nach** dem Abschneiden umgebender Leerzeichen und Tabs, aber vor
    allem anderen: ein Zeilenumbruch in einer Adresse ist kein Tippfehler,
    sondern der klassische Header-Injection-Vektor
    (`opfer@example.com\nBcc: ...`), und muss deshalb abgelehnt statt bereinigt
    werden.
    """
    if any(character.isspace() for character in candidate):
        return Err(EmailHasWhitespace(candidate))
    return Ok(candidate)


def has_exactly_one_at(candidate: str) -> Result[str, EmailError]:
    """Genau ein `@`.

    Ein zweites `@` waere nur in einem quoted Local-Part (`"a@b"@c.de`) zulaessig -
    diese Form wird hier bewusst nicht unterstuetzt, weil sie in der Praxis nicht
    vorkommt und jede nachfolgende Regel verkomplizieren wuerde.
    """
    if (count := candidate.count("@")) != 1:
        return Err(EmailNeedsExactlyOneAtSign(candidate, count))
    return Ok(candidate)


def has_both_parts(candidate: str) -> Result[str, EmailError]:
    """Vor und hinter dem `@` steht etwas."""
    local, domain = _split(candidate)
    if not local:
        return Err(EmailLocalPartMissing(candidate))
    return Ok(candidate) if domain else Err(EmailDomainMissing(candidate))


def local_part_fits_length(candidate: str) -> Result[str, EmailError]:
    """Der Local-Part ueberschreitet die zulaessige Laenge nicht."""
    local, _ = _split(candidate)
    if len(local) > MAX_LOCAL_LENGTH:
        return Err(EmailLocalPartTooLong(local, MAX_LOCAL_LENGTH))
    return Ok(candidate)


def local_part_uses_allowed_characters(candidate: str) -> Result[str, EmailError]:
    """Der Local-Part besteht aus alphanumerischen Zeichen und erlaubten Sonderzeichen."""
    local, _ = _split(candidate)
    if invalid := {c for c in local if not c.isalnum() and c not in _LOCAL_SPECIALS}:
        return Err(EmailLocalPartHasInvalidCharacters(local, tuple(sorted(invalid))))
    return Ok(candidate)


def local_part_places_dots_legally(candidate: str) -> Result[str, EmailError]:
    """Kein fuehrender, abschliessender oder doppelter Punkt im Local-Part."""
    local, _ = _split(candidate)
    if local.startswith(".") or local.endswith(".") or ".." in local:
        return Err(EmailLocalPartHasMisplacedDot(local))
    return Ok(candidate)


def domain_fits_length(candidate: str) -> Result[str, EmailError]:
    """Die Domain ueberschreitet die zulaessige Gesamtlaenge nicht."""
    _, domain = _split(candidate)
    if len(domain) > MAX_DOMAIN_LENGTH:
        return Err(EmailDomainTooLong(domain, MAX_DOMAIN_LENGTH))
    return Ok(candidate)


def domain_is_valid(candidate: str, idn: IdnEncoder) -> Result[str, EmailError]:
    """Die Domain ist entweder ein IP-Literal in Klammern oder eine Label-Folge.

    Einzige Regel mit einer Abhaengigkeit: internationalisierte Labels muessen in
    ihre ASCII-Form gebracht werden, bevor die Laengengrenze ueberhaupt sinnvoll
    geprueft werden kann.
    """
    _, domain = _split(candidate)
    if domain.startswith("[") and domain.endswith("]"):
        return _address_literal_is_valid(candidate, domain[1:-1])
    return _labels_are_valid(candidate, domain, idn)


def _address_literal_is_valid(candidate: str, literal: str) -> Result[str, EmailError]:
    """Ein Adress-Literal `[...]` muss eine gueltige IPv4- oder IPv6-Adresse sein."""
    try:
        ip_address(literal)
    except ValueError:
        return Err(EmailAddressLiteralInvalid(literal))
    return Ok(candidate)


def _labels_are_valid(candidate: str, domain: str, idn: IdnEncoder) -> Result[str, EmailError]:
    """Jedes durch Punkt getrennte Label ist fuer sich genommen gueltig.

    Ein Label pro Regel, verkettet mit demselben `chain` wie die Regeln der
    Gesamtadresse: das erste ungueltige Label gewinnt, die folgenden laufen gar
    nicht mehr.
    """
    per_label = (
        partial(_label_is_valid, label=label, domain=domain, idn=idn) for label in domain.split(".")
    )
    return chain(*per_label)(candidate)


def _label_is_valid(
    candidate: str, *, label: str, domain: str, idn: IdnEncoder
) -> Result[str, EmailError]:
    """Ein einzelnes Label - gepruefte Adresse durchgereicht, damit die Kette weiterlaeuft."""
    return (
        _label_is_not_empty(label, domain)
        .bind(_label_has_no_edge_hyphen)
        .bind(lambda checked: _ascii_form_of(checked, idn))
        .bind(lambda ascii_label: _ascii_label_fits_the_limits(label, ascii_label))
        .map(lambda _: candidate)
    )


def _label_is_not_empty(label: str, domain: str) -> Result[str, EmailError]:
    """Ein leeres Label deckt drei Faelle ab: fuehrender, doppelter, abschliessender Punkt."""
    return Ok(label) if label else Err(EmailDomainHasEmptyLabel(domain))


def _label_has_no_edge_hyphen(label: str) -> Result[str, EmailError]:
    """Ein Label faengt nicht mit einem Bindestrich an und hoert nicht mit einem auf."""
    if label.startswith("-") or label.endswith("-"):
        return Err(EmailDomainLabelHasEdgeHyphen(label))
    return Ok(label)


def _ascii_label_fits_the_limits(label: str, ascii_label: str) -> Result[str, EmailError]:
    """Laenge und Zeichenvorrat gelten fuer die ASCII-Form - gemeldet wird das Original."""
    if len(ascii_label) > MAX_LABEL_LENGTH:
        return Err(EmailDomainLabelTooLong(label, len(ascii_label), MAX_LABEL_LENGTH))
    if any(not _is_ascii_label_character(c) for c in ascii_label):
        return Err(EmailDomainLabelHasInvalidCharacters(label))
    return Ok(ascii_label)


def _ascii_form_of(label: str, idn: IdnEncoder) -> Result[str, EmailError]:
    """Die ASCII-Form eines Labels - fuer ASCII-Labels es selbst.

    Nur internationalisierte Labels gehen ueber den Port. Die Laengengrenze gilt
    laut RFC 1034 fuer die ASCII-Form, ein Unicode-Label also erst nach der
    Punycode-Umwandlung: `उदाहरण` sind sieben Zeichen, aber sechzehn als
    `xn--p1b6ci4b4b3a`.
    """
    return Ok(label) if label.isascii() else idn.to_ascii(label)


def _is_ascii_label_character(character: str) -> bool:
    """Erlaubt sind Alphanumerik und der Bindestrich - Unterstriche nicht."""
    return character.isalnum() or character == "-"


def is_not_blank(candidate: str) -> Result[str, EmailError]:
    """Es wurde ueberhaupt eine Adresse angegeben - und sie kommt getrimmt zurueck.

    Erste Regel der Kette, nicht ein `strip` daneben: sonst saehe jede folgende
    Regel einen Wert, den sie erneut anfassen muesste
    (.rules/python/python-rule-pattern.md). Und `"   "` meldet damit "keine
    Adresse angegeben" statt des irrefuehrenden "kein At-Zeichen".

    Getrimmt wird nur Leerzeichen und Tabulator, nicht wie bei `not_blank` jeder
    Leerraum: ein abschliessender Zeilenumbruch soll `has_no_whitespace` in die
    Haende fallen und die Adresse verwerfen. Geurteilt wird trotzdem gegen den
    voll getrimmten Wert: ein Wert aus reinem Leerraum ist keine Adresse,
    sondern leer.
    """
    return Ok(candidate.strip(" \t")) if candidate.strip() else Err(EmailIsEmpty())


def is_normalized(candidate: str) -> Result[str, EmailError]:
    """Bringe die Adresse auf ihre Vergleichsform: case-folded.

    Die einzige Regel dieser Kette, die nie scheitert - sie normalisiert, was
    jede folgende voraussetzt. Getrimmt hat bereits `is_not_blank`.
    """
    return Ok(candidate.casefold())


_RULES: ResultRule[str, EmailError] = chain(
    is_not_blank,
    is_normalized,
    has_no_whitespace,
    has_exactly_one_at,
    has_both_parts,
    local_part_fits_length,
    local_part_uses_allowed_characters,
    local_part_places_dots_legally,
    domain_fits_length,
)

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `parse` und `hydrate` unten haben ihn."""


@final
@dataclass(frozen=True, slots=True)
class Email:
    """Bereits normalisierte E-Mail-Adresse (getrimmt, case-folded).

    Die Normalisierung passiert in `parse` und nirgends sonst - damit ist die
    Eindeutigkeitspruefung des Nutzerbestands zwangslaeufig case-insensitiv.
    """

    value: str
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `parse` oder `hydrate` ging.

        Geprueft wird der **Weg**, nicht der Wert: `domain_is_valid` braucht den
        IDN-Port, und ein `__post_init__` bekommt ihn nicht
        (docs/decisions/2026-08-26-2030-die-wurzel-haelt-ihre-invarianten-selbst.md).
        """
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def parse(cls, raw: str, idn: IdnEncoder) -> Result[Self, EmailError]:
        """Normalisiere und pruefe eine moeglicherweise ungueltige Eingabe.

        `domain_is_valid` steht nicht in `_RULES`, weil sie als einzige den
        IDN-Port braucht - `bind` gibt ihr dieselbe Fail-fast-Semantik.
        """
        return (
            _RULES(raw)
            .bind(lambda checked: domain_is_valid(checked, idn))
            .map(lambda checked: cls(checked, key=_KEY))
        )

    @classmethod
    def hydrate(cls, raw: str, idn: IdnEncoder) -> Email:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw, idn):
            case Ok(value=email):
                return email
            case Err():
                msg = f"unreachable: {raw!r} wurde vorgelagert validiert"
                raise AssertionError(msg)
