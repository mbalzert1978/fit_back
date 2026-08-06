"""Value Object Email - case-insensitiv normalisiert, aus einzelnen Regeln geprueft.

Bewusst **kein** Regex fuer die Gesamtadresse. Ein Adress-Regex behauptet mehr,
als ein Leser ihm ansehen kann: Label-Laenge, fuehrende/abschliessende
Bindestriche, Unterstriche in der Domain, IP-Literale, IPv6-Gruppenzahl - all das
steckt entweder unlesbar drin oder gar nicht. Stattdessen eine `chain(...)` aus
einzeln benannten Fail-fast-Regeln: jede beantwortet genau eine Frage, jede
erklaert ihren Fehlschlag selbst, und die Testtabelle in
`contexts/identity/tests/domain/test_email.py` prueft sie Fall fuer Fall.
"""

from dataclasses import dataclass
from ipaddress import ip_address
from typing import final

from src.shared_kernel import Err, Ok, Result
from src.shared_kernel.validation import ResultRule, chain

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


def has_no_whitespace(candidate: str) -> Result[str, str]:
    """Kein Leerraum - irgendwo in der Adresse.

    Laeuft **nach** dem Abschneiden umgebender Leerzeichen und Tabs, aber vor
    allem anderen: ein Zeilenumbruch in einer Adresse ist kein Tippfehler,
    sondern der klassische Header-Injection-Vektor
    (`opfer@example.com\\nBcc: ...`), und muss deshalb abgelehnt statt bereinigt
    werden.
    """
    if any(character.isspace() for character in candidate):
        return Err("E-Mail-Adresse darf keinen Leerraum enthalten")
    return Ok(candidate)


def has_exactly_one_at(candidate: str) -> Result[str, str]:
    """Genau ein `@`.

    Ein zweites `@` waere nur in einem quoted Local-Part (`"a@b"@c.de`) zulaessig -
    diese Form wird hier bewusst nicht unterstuetzt, weil sie in der Praxis nicht
    vorkommt und jede nachfolgende Regel verkomplizieren wuerde.
    """
    if candidate.count("@") != 1:
        return Err("E-Mail-Adresse braucht genau ein '@'")
    return Ok(candidate)


def has_both_parts(candidate: str) -> Result[str, str]:
    """Vor und hinter dem `@` steht etwas."""
    local, domain = _split(candidate)
    if not local:
        return Err("E-Mail-Adresse braucht einen Teil vor dem '@'")
    if not domain:
        return Err("E-Mail-Adresse braucht einen Teil hinter dem '@'")
    return Ok(candidate)


def local_part_fits_length(candidate: str) -> Result[str, str]:
    """Der Local-Part ueberschreitet die zulaessige Laenge nicht."""
    local, _ = _split(candidate)
    if len(local) > MAX_LOCAL_LENGTH:
        return Err(f"Teil vor dem '@' darf hoechstens {MAX_LOCAL_LENGTH} Zeichen lang sein")
    return Ok(candidate)


def local_part_uses_allowed_characters(candidate: str) -> Result[str, str]:
    """Der Local-Part besteht aus alphanumerischen Zeichen und erlaubten Sonderzeichen."""
    local, _ = _split(candidate)
    if invalid := {c for c in local if not c.isalnum() and c not in _LOCAL_SPECIALS}:
        return Err(f"unzulaessige Zeichen vor dem '@': {''.join(sorted(invalid))!r}")
    return Ok(candidate)


def local_part_places_dots_legally(candidate: str) -> Result[str, str]:
    """Kein fuehrender, abschliessender oder doppelter Punkt im Local-Part."""
    local, _ = _split(candidate)
    if local.startswith(".") or local.endswith("."):
        return Err("Teil vor dem '@' darf nicht mit einem Punkt beginnen oder enden")
    if ".." in local:
        return Err("Teil vor dem '@' darf keine zwei aufeinanderfolgenden Punkte enthalten")
    return Ok(candidate)


def domain_fits_length(candidate: str) -> Result[str, str]:
    """Die Domain ueberschreitet die zulaessige Gesamtlaenge nicht."""
    _, domain = _split(candidate)
    if len(domain) > MAX_DOMAIN_LENGTH:
        return Err(f"Domain darf hoechstens {MAX_DOMAIN_LENGTH} Zeichen lang sein")
    return Ok(candidate)


def domain_is_valid(candidate: str) -> Result[str, str]:
    """Die Domain ist entweder ein IP-Literal in Klammern oder eine Label-Folge."""
    _, domain = _split(candidate)
    if domain.startswith("[") and domain.endswith("]"):
        return _address_literal_is_valid(candidate, domain[1:-1])
    return _labels_are_valid(candidate, domain)


def _address_literal_is_valid(candidate: str, literal: str) -> Result[str, str]:
    """Ein Adress-Literal `[...]` muss eine gueltige IPv4- oder IPv6-Adresse sein."""
    try:
        ip_address(literal)
    except ValueError:
        return Err(f"kein gueltiges IP-Adress-Literal: {literal!r}")
    return Ok(candidate)


def _labels_are_valid(candidate: str, domain: str) -> Result[str, str]:
    """Jedes durch Punkt getrennte Label ist fuer sich genommen gueltig.

    Ein leeres Label deckt gleich drei Faelle ab: fuehrender Punkt, doppelter
    Punkt und - der haeufigste Tippfehler - der abschliessende Punkt.
    """
    for label in domain.split("."):
        if not label:
            return Err("Domain darf kein leeres Label enthalten")
        if len(label) > MAX_LABEL_LENGTH:
            return Err(f"Domain-Label darf hoechstens {MAX_LABEL_LENGTH} Zeichen lang sein")
        if label.startswith("-") or label.endswith("-"):
            return Err("Domain-Label darf nicht mit einem Bindestrich beginnen oder enden")
        if any(not _is_label_character(character) for character in label):
            return Err(f"unzulaessige Zeichen im Domain-Label: {label!r}")
    return Ok(candidate)


def _is_label_character(character: str) -> bool:
    """Erlaubt sind ASCII-Alphanumerik, der Bindestrich und jedes Nicht-ASCII-Zeichen.

    Die Nicht-ASCII-Oeffnung traegt die internationalisierten Domainnamen
    (`उदाहरण.परीक्षा`). `str.isalnum()` allein reicht dafuer nicht: kombinierende
    Zeichen wie das Virama sind Marken, keine Alphanumerik, und wuerden eine
    voellig gueltige IDN-Domain ablehnen. Unterstriche bleiben verboten - sie
    sind ASCII und nicht alphanumerisch.
    """
    return not character.isascii() or character.isalnum() or character == "-"


_RULES: ResultRule[str, str] = chain(
    has_no_whitespace,
    has_exactly_one_at,
    has_both_parts,
    local_part_fits_length,
    local_part_uses_allowed_characters,
    local_part_places_dots_legally,
    domain_fits_length,
    domain_is_valid,
)


@final
@dataclass(frozen=True, slots=True)
class Email:
    """Bereits normalisierte E-Mail-Adresse (getrimmt, case-folded).

    Die Normalisierung passiert in `parse` und nirgends sonst - damit ist die
    Eindeutigkeitspruefung des Nutzerbestands zwangslaeufig case-insensitiv.
    """

    value: str

    @classmethod
    def parse(cls, raw: str) -> Result[Email, str]:
        """Normalisiere und pruefe eine moeglicherweise ungueltige Eingabe.

        Abgeschnitten werden **nur** umgebende Leerzeichen und Tabs - das sind
        Kopier-Artefakte. Zeilenumbrueche und andere Steuerzeichen werden
        bewusst nicht bereinigt, sondern von `has_no_whitespace` abgelehnt.
        """
        return _RULES(raw.strip(" \t").casefold()).map(cls)

    @classmethod
    def hydrate(cls, raw: str) -> Email:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw):
            case Ok(value=email):
                return email
            case Err():
                raise AssertionError(f"unreachable: {raw!r} wurde vorgelagert validiert")
