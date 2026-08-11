"""
Small formatting helpers for values that insurer forms validate
strictly — currently just Canadian postal codes.
"""

import re

_EM_DASH = "\u2014"


def sanitize_display_text(text: str | None) -> str:
    """Replace em dashes with colons for UI and report copy."""
    if not text:
        return ""
    return text.replace(f" {_EM_DASH} ", ": ").replace(_EM_DASH, ": ")


def postal_code_variants(raw: str) -> list[str]:
    """Return both plausible formats for a Canadian postal code, in
    the order to try them: compact first (no space), since masked
    input widgets often auto-insert their own formatting and can
    reject a manually-typed space, then the spaced format as fallback
    for sites that validate strictly against 'A1A 1A1'."""
    cleaned = "".join(c for c in raw if c.isalnum()).upper()
    if len(cleaned) != 6:
        return [raw.strip()]
    return [cleaned, f"{cleaned[:3]} {cleaned[3:]}"]


def normalize_postal_code(raw: str) -> str:
    """Normalize to 'A1A 1A1' format. If the input doesn't contain
    exactly 6 alphanumeric characters after stripping spaces/dashes,
    return it unchanged rather than guessing — a malformed postal
    code should surface as a real validation error on the form, not
    be silently mangled into something that looks valid but isn't."""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
    if len(cleaned) != 6:
        return raw.strip()
    return f"{cleaned[:3]} {cleaned[3:]}"
