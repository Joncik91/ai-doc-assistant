"""PII detection helpers for ingestion warnings."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(slots=True)
class PiiFinding:
    """A non-blocking PII indicator found in a document."""

    category: str
    count: int
    warning: str


EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2}\d{4}\b")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def _luhn_check(value: str) -> bool:
    digits = [int(character) for character in value if character.isdigit()]
    if len(digits) < 13:
        return False

    checksum = 0
    should_double = False
    for digit in reversed(digits):
        if should_double:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
        should_double = not should_double
    return checksum % 10 == 0


def scan_text_for_pii(text: str) -> list[PiiFinding]:
    """Return warnings for likely PII patterns without blocking ingestion."""

    normalized = text or ""
    findings: list[PiiFinding] = []

    matches = EMAIL_PATTERN.findall(normalized)
    if matches:
        findings.append(
            PiiFinding(
                category="email",
                count=len(matches),
                warning=f"Possible email addresses detected ({len(matches)}).",
            )
        )

    matches = PHONE_PATTERN.findall(normalized)
    if matches:
        findings.append(
            PiiFinding(
                category="phone",
                count=len(matches),
                warning=f"Possible phone numbers detected ({len(matches)}).",
            )
        )

    matches = SSN_PATTERN.findall(normalized)
    if matches:
        findings.append(
            PiiFinding(
                category="ssn",
                count=len(matches),
                warning=f"Possible SSN patterns detected ({len(matches)}).",
            )
        )

    card_candidates = CREDIT_CARD_PATTERN.findall(normalized)
    valid_cards = [candidate for candidate in card_candidates if _luhn_check(candidate)]
    if valid_cards:
        findings.append(
            PiiFinding(
                category="credit_card",
                count=len(valid_cards),
                warning=f"Possible credit card numbers detected ({len(valid_cards)}).",
            )
        )

    return findings
