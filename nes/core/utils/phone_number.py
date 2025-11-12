"""Utilities for normalizing Nepali phone numbers."""

import re
from typing import Optional


def normalize_nepali_phone_number(phone: Optional[str]) -> Optional[str]:
    """Normalize Nepali phone numbers to international format.

    Args:
        phone: Raw phone number string

    Returns:
        Normalized phone number in format +977XXXXXXXXXX
        Returns None if invalid

    Examples:
        >>> normalize_nepali_phone_number("9851081379")
        '+9779851081379'
        >>> normalize_nepali_phone_number("01-4569033")
        '+97714569033'
        >>> normalize_nepali_phone_number("6610974")
        '+9776610974'
    """
    if not phone:
        return None

    phone = str(phone).strip()
    digits = re.sub(r"\D", "", phone)

    if not digits:
        return None

    # Remove 00977 or 977 if present
    if digits.startswith("00977"):
        digits = digits[5:]
    elif digits.startswith("977"):
        digits = digits[3:]

    # Remove leading zeros
    digits = digits.lstrip("0")

    if not digits or len(digits) > 10:
        return None

    return f"+977{digits}"
