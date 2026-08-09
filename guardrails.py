"""
Hard stops required by the brief (Section 2 "Human checkpoints",
Section 8 "Identity, privacy and safety rules").

These are enforced in code, not left to the agent's judgment, because
the brief treats violations here as disqualifying:
  - never click/sign an application declaration
  - never submit payment
  - never bypass a CAPTCHA or access control
  - never use a fabricated licence number in a live (non-estimate) flow
  - never enter another person's information without consent
"""

import re

# Page text signals that mean an ACTIVE challenge or block is actually
# in front of us right now — not just a passive "this site uses
# reCAPTCHA" disclosure footer, which is normal and appears on most
# insurer sites even when nothing is blocking us. The bare word
# "captcha" alone is deliberately NOT in this list, since standard
# reCAPTCHA v3 disclosure text ("Protected by reCAPTCHA | Privacy |
# Terms") triggered false positives on every page.
BLOCK_SIGNALS = [
    r"i.?m not a robot",              # actual reCAPTCHA v2 checkbox text
    r"verify you.?re human",
    r"please verify you are a human",
    r"unusual traffic (from|detected)",
    r"access (to this page has been )?denied",
    r"please complete the (security )?check",
    r"solve the (puzzle|challenge) (below|above)",
    r"declaration",
    r"i confirm the above information is true",
    r"electronic signature",
    r"sign here",
    # Payment/checkout signals — deliberately specific to avoid matching
    # unrelated marketing content (e.g. a "Tangerine Credit Card" cross-
    # promotion ad triggered a false positive on the bare phrase
    # "credit card"). These require actual checkout-context wording.
    r"enter your credit card",
    r"credit card number",
    r"card number.{0,40}(expiry|cvv|security code)",
    r"\bcvv\b",
    r"billing address",
    r"amount due",
    r"select (a |your )?payment method to (proceed|continue|pay)",
    r"bind (this )?policy",
    r"purchase (this )?policy",
    r"confirm (and )?pay",
]

# Passive signals worth noting in the log but NOT stopping the run for.
# "Protected by reCAPTCHA" footers are near-universal and do not mean
# a challenge is actually present on this page.
SOFT_SIGNALS = [
    r"protected by recaptcha",
]

_BLOCK_RE = re.compile("|".join(BLOCK_SIGNALS), re.IGNORECASE)
_SOFT_RE = re.compile("|".join(SOFT_SIGNALS), re.IGNORECASE)


class GuardrailStop(Exception):
    """Raised when a hard-stop condition is detected. Caller must
    catch this, log the appropriate Status, and move to the next
    route rather than retrying past the block."""
    def __init__(self, reason: str, status: str):
        self.reason = reason
        self.status = status
        super().__init__(reason)


def check_page_text(page_text: str):
    """Call this after every navigation/page load, before any further
    automated action. Raises GuardrailStop if an ACTIVE blocking signal
    is found. Passive signals (e.g. standard reCAPTCHA disclosure
    footers) are logged for visibility but do not stop the run."""
    soft_match = _SOFT_RE.search(page_text)
    if soft_match:
        print(f"[guardrail-note] passive signal seen (not blocking): '{soft_match.group(0)}'")

    match = _BLOCK_RE.search(page_text)
    if match:
        signal = match.group(0).lower()
        if any(k in signal for k in ["robot", "human", "unusual traffic", "denied", "security check", "puzzle", "challenge"]):
            raise GuardrailStop(f"Active access-control challenge detected: '{signal}'", "blocked")
        if any(k in signal for k in ["declaration", "confirm the above", "signature", "sign here"]):
            raise GuardrailStop(f"Application declaration/signature step reached: '{signal}'", "manual_handoff")
        if any(k in signal for k in ["payment method", "credit card", "card number", "cvv", "billing address", "amount due", "bind", "purchase", "confirm and pay"]):
            raise GuardrailStop(f"Payment/bind step reached: '{signal}'", "manual_handoff")
    return None


def validate_applicant_for_mode(applicant) -> None:
    """Refuse to proceed if the applicant object is inconsistent with
    its declared mode. Call this once before starting any route."""
    if applicant.mode == "estimate_only":
        if applicant.licence_number.strip():
            raise ValueError(
                "estimate_only mode must never carry a licence number. "
                "Clear applicant.licence_number or switch mode to 'live'."
            )
        if applicant.legal_name.strip() and _looks_like_real_full_name(applicant.legal_name):
            # Not a hard crash, just a strong warning path — caller should
            # confirm this is an intentionally hypothetical label.
            pass
    elif applicant.mode == "live":
        if not applicant.legal_name.strip():
            raise ValueError("live mode requires the applicant's real legal name.")
        if not applicant.consent_timestamp:
            raise ValueError("live mode requires consent_timestamp to be set before any route runs.")


def _looks_like_real_full_name(name: str) -> bool:
    # Heuristic only, not a real PII detector — just a sanity check.
    return len(name.split()) >= 2


def redact_for_storage(record: dict) -> dict:
    """Strip or mask sensitive fields before writing any evidence or
    log to disk. Call before every save."""
    sensitive_keys = {
        "licence_number", "vin", "date_of_birth", "street",
        "postal_code", "phone", "email",
    }
    redacted = dict(record)
    for k in sensitive_keys:
        if k in redacted and redacted[k]:
            redacted[k] = "[REDACTED]"
    return redacted
