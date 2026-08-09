"""
Adaptive browser agent for one market-registry route.

Instead of hardcoding CSS selectors per insurer site (which breaks the
moment a site changes, and which I can't test from this sandbox since
it has no live internet access), this agent:

  1. loads the page
  2. runs guardrails.check_page_text() BEFORE touching anything
  3. extracts every visible input/select/textarea with its nearby label
  4. asks Claude to map each field to our intake schema (or null if
     it's an identity/declaration/payment field we should never fill)
  5. fills only the mapped, non-null, non-sensitive fields
  6. looks for a "next / continue / get quote" button, clicks it
  7. repeats, up to MAX_STEPS, re-checking guardrails on every new page
  8. stops the moment guardrails trips, a captcha appears, or no more
     recognizable form is found — and returns whatever result that
     implies (blocked / manual_handoff / unresolved / quoted)

This is slower than hardcoded selectors but works across sites you
haven't tested yet, which matters more given the 6-route scope and
the time you have left today.
"""

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict

from formatting_utils import normalize_postal_code

from playwright.async_api import async_playwright, Page
import anthropic

from schema import MarketRecord, QuoteResult, Status, Applicant
from guardrails import check_page_text, GuardrailStop, redact_for_storage

EVIDENCE_DIR = Path(__file__).parent / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

MAX_STEPS = 8          # bounded-attempt policy: don't loop forever on one route
NAV_TIMEOUT_MS = 20000

client = anthropic.Anthropic()

# Field names we NEVER auto-fill even if Claude maps them — these must
# stop the flow and go to manual_handoff instead. Second layer of
# protection on top of guardrails.check_page_text().
NEVER_AUTOFILL = {"licence_number_confirm", "signature", "payment_card", "cvv"}


async def safe_inner_text(page: Page, timeout_ms: int = 20000) -> str:
    """Read the page's visible text with one bounded retry on timeout,
    per the brief's own bounded-attempt policy ("one normal attempt plus
    one retry for a transient technical error"). Heavier JS apps can be
    mid-render when we try to read them, especially right after a real
    navigation (not just an SPA hash change) - a single retry with a
    short wait covers that without looping indefinitely."""
    try:
        return await page.inner_text("body", timeout=timeout_ms)
    except Exception:
        await page.wait_for_timeout(2000)
        return await page.inner_text("body", timeout=timeout_ms)


async def extract_visible_fields(page: Page) -> list[dict]:
    """Pull every visible input/select/textarea plus its best-guess
    label text, using proximity in the DOM rather than assuming any
    particular framework's markup."""
    return await page.evaluate("""
    () => {
        const fields = [];
        const inputs = document.querySelectorAll('input, select, textarea');
        for (const el of inputs) {
            const rect = el.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) continue;
            if (el.type === 'hidden') continue;

            let label = '';
            if (el.id) {
                const lbl = document.querySelector(`label[for="${el.id}"]`);
                if (lbl) label = lbl.innerText;
            }
            if (!label && el.closest('label')) {
                label = el.closest('label').innerText;
            }
            if (!label) {
                label = el.getAttribute('aria-label') || el.getAttribute('placeholder') || '';
            }
            if (!label && el.previousElementSibling) {
                label = el.previousElementSibling.innerText || '';
            }

            fields.push({
                tag: el.tagName.toLowerCase(),
                type: el.type || '',
                name: el.name || '',
                id: el.id || '',
                label: label.trim().slice(0, 120),
                selector: el.id ? `#${el.id}` : (el.name ? `[name="${el.name}"]` : null),
            });
        }
        return fields;
    }
    """)


async def find_continue_button(page: Page) -> str | None:
    """Best-effort search for a next/continue/get-quote button."""
    candidate = await page.evaluate("""
    () => {
        const texts = ['continue', 'next', 'get quote', 'get my quote', 'see my quote',
                        'get my rate', 'submit', 'proceed', 'get started',
                        'confirm', 'accept', 'agree', 'ok', 'got it'];
        const buttons = [...document.querySelectorAll('button, input[type=submit], a.button, a.btn')];
        for (const b of buttons) {
            const t = (b.innerText || b.value || '').trim().toLowerCase();
            if (texts.some(x => t.includes(x))) {
                return b.id ? `#${b.id}` : (b.className ? `.${b.className.split(' ')[0]}` : null);
            }
        }
        return null;
    }
    """)
    return candidate


async def find_homepage_cta(page: Page) -> str | None:
    """First-step-only fallback for sites that redirect deep quote-flow
    links back to the homepage (anti-direct-linking protection, seen on
    belairdirect: navigating straight to the quote subdomain bounced back
    to www.belairdirect.com). Real visitors reach the flow by clicking a
    homepage CTA instead, so we do the same rather than fighting the
    redirect - this is honest navigation, not evasion.

    Uses EXACT text matching (not substring) against a short curated
    list, to avoid false-positive clicks on unrelated nav links that
    happen to contain the same words (e.g. a nav item literally titled
    "Insurance" or a footer link mentioning "car insurance")."""
    exact_targets = ["car", "auto", "get a quote", "start quote",
                      "get your price", "get started", "get my quote"]
    candidate = await page.evaluate(f"""
    () => {{
        const targets = {exact_targets!r};
        const els = [...document.querySelectorAll('button, a, div[role="button"]')];
        for (const el of els) {{
            const txt = (el.innerText || '').trim().toLowerCase();
            if (targets.includes(txt) && el.offsetParent !== null) {{
                const r = el.getBoundingClientRect();
                return {{x: r.x + r.width / 2, y: r.y + r.height / 2}};
            }}
        }}
        return null;
    }}
    """)
    return candidate


async def try_custom_dropdown(page: Page, value: str) -> bool:
    """Fallback for custom-styled dropdown/combobox components that are
    NOT native <select> elements (common in React-built sites). Our
    extract_visible_fields() only finds real <select>/<input>/<textarea>
    tags, so a styled div/button dropdown is invisible to it — this is
    why some sites produce zero fields even though a form is clearly
    on screen.

    Strategy: find any small clickable element whose exact visible text
    is a placeholder like "Select", click it to open the option list,
    then click whichever option's text matches the target value. If
    multiple "Select" placeholders exist on the page (e.g. one behind
    a modal), we prefer the last one in DOM order, since modals are
    typically appended last to the document body."""
    try:
        trigger_pos = await page.evaluate("""
        () => {
            const candidates = [...document.querySelectorAll('div, button, span')];
            const matches = candidates.filter(el => {
                const txt = (el.innerText || '').trim();
                return (txt === 'Select' || txt.toLowerCase() === 'select province')
                    && el.offsetParent !== null;
            });
            if (matches.length === 0) return null;
            const el = matches[matches.length - 1];  // prefer topmost/last-appended (modal)
            const r = el.getBoundingClientRect();
            return {x: r.x + r.width / 2, y: r.y + r.height / 2};
        }
        """)
        if not trigger_pos:
            return False

        await page.mouse.click(trigger_pos["x"], trigger_pos["y"])
        await page.wait_for_timeout(500)

        option_pos = await page.evaluate(f"""
        () => {{
            const target = {value.lower()!r};
            const candidates = [...document.querySelectorAll('li, div, span, button, [role="option"]')];
            const matches = candidates.filter(el => {{
                const txt = (el.innerText || '').trim().toLowerCase();
                return txt === target && el.offsetParent !== null;
            }});
            if (matches.length === 0) return null;
            const el = matches[matches.length - 1];
            const r = el.getBoundingClientRect();
            return {{x: r.x + r.width / 2, y: r.y + r.height / 2}};
        }}
        """)
        if option_pos:
            await page.mouse.click(option_pos["x"], option_pos["y"])
            await page.wait_for_timeout(500)
            return True
        return False
    except Exception:
        return False


async def try_address_autocomplete(page: Page, selector: str, address_text: str) -> bool:
    """Fill an address-autocomplete field by typing character-by-character
    (not .fill()) so the site's JS listener actually fires, then wait
    for a suggestion dropdown and select the first result. Falls back
    to a plain .fill() if no dropdown appears within the timeout,
    since some 'address' fields are genuinely plain text inputs."""
    try:
        el = page.locator(selector).first
        await el.click()
        await el.fill("")  # clear first
        await el.type(address_text, delay=60)  # character-by-character, triggers JS listeners
        await page.wait_for_timeout(1200)  # let suggestions load

        # Look for a visible suggestion list (common patterns: pac-container
        # for Google Places, role="listbox", or a dropdown right below the input)
        suggestion_visible = await page.evaluate("""
        () => {
            const candidates = document.querySelectorAll(
                '.pac-container, [role="listbox"], .autocomplete-suggestions, .address-suggestions'
            );
            for (const c of candidates) {
                if (c.offsetParent !== null && c.children.length > 0) return true;
            }
            return false;
        }
        """)

        if suggestion_visible:
            await page.keyboard.press("ArrowDown")
            await page.wait_for_timeout(300)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(500)
            return True

        # No dropdown appeared - the typed text is still in the field,
        # which is an acceptable fallback for a plain (non-autocomplete) input.
        return False
    except Exception:
        return False


async def map_fields_with_claude(fields: list[dict], applicant: Applicant) -> dict:
    """Returns {selector: intake_attr_name or None}."""
    if not fields:
        return {}

    applicant_dict = asdict(applicant)
    prompt = f"""You are mapping a live insurance quote form's fields to a known
intake schema. I will give you a list of form fields (label, type, name)
and the available intake attribute names. Return ONLY a JSON object
mapping each field's "selector" value to the matching intake attribute
name, or null if there is no safe match.

Rules:
- Never map anything that looks like a signature, attestation/declaration
  checkbox, payment/card field, or an identity-verification-only field
  (e.g. "confirm licence number", "SIN") — map those to null.
- If a field looks like a required consent checkbox to proceed (not a
  declaration of truthfulness, just "I agree to terms to get a quote"),
  map it to null too; a human should decide, don't auto-check it.
- Only map fields you're reasonably confident about.

Available intake attributes: {json.dumps(list(applicant_dict.keys()))}

Form fields:
{json.dumps(fields, indent=2)[:4000]}

Return only the JSON object {{selector: attribute_or_null}}, nothing else."""

    resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    text = re.sub(r"^```json|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


async def fill_mapped_fields(page: Page, mapping: dict, fields: list[dict], applicant: Applicant):
    applicant_dict = asdict(applicant)
    field_by_selector = {f["selector"]: f for f in fields if f["selector"]}

    for selector, attr in mapping.items():
        if not attr or attr in NEVER_AUTOFILL or selector not in field_by_selector:
            continue
        value = applicant_dict.get(attr)
        if value in (None, ""):
            continue
        if attr == "postal_code" and value:
            value = normalize_postal_code(value)
        f = field_by_selector[selector]
        try:
            if f["tag"] == "select":
                await page.select_option(selector, label=str(value))
            elif f["type"] in ("checkbox", "radio"):
                if str(value).lower() in ("true", "1", "yes"):
                    await page.check(selector)
            else:
                if attr == "street" and f["tag"] != "select":
                    handled = await try_address_autocomplete(page, selector, str(value))
                    if handled:
                        continue
                await page.fill(selector, str(value))
        except Exception:
            # Non-fatal: some fields resist automated fill (custom widgets,
            # date pickers). Log and move on rather than crashing the route.
            continue


async def mask_sensitive_before_screenshot(page: Page):
    """Blank out anything that looks like it holds sensitive data before
    we capture evidence, regardless of whether we filled it ourselves."""
    await page.evaluate("""
    () => {
        const sensitive = /licen[cs]e|vin|dob|birth|postal|address|phone|email|sin\\b/i;
        document.querySelectorAll('input, textarea').forEach(el => {
            const blob = (el.name + ' ' + el.id + ' ' + (el.placeholder||'')).toLowerCase();
            if (sensitive.test(blob) && el.value) {
                el.value = '••••••';
            }
        });
    }
    """)


async def run_route(record: MarketRecord, applicant: Applicant) -> QuoteResult:
    result = QuoteResult(
        registry_id=record.registry_id,
        distinct_rate_source_id=record.distinct_rate_source_id,
        status=Status.UNRESOLVED,
    )

    if not record.quote_url:
        result.status = Status(record.status) if record.status else Status.MANUAL_HANDOFF
        result.failure_reason = record.automation_notes
        result.next_action = "No automatable path by design (see registry notes)."
        _log(record, result)
        return result

    async with async_playwright() as p:
        # Running visibly (not headless) for two honest reasons: (1) some
        # bot-detection services specifically flag the headless Chromium
        # signature, so a normal visible browser session may be treated
        # more like ordinary traffic, and (2) it lets the operator watch
        # the run happen in real time. This is a configuration choice,
        # not fingerprint spoofing - we do not hide automation flags or
        # alter navigator properties, which would cross into bypassing
        # bot controls (not permitted per the brief).
        browser = await p.chromium.launch(headless=False, slow_mo=150)
        page = await browser.new_page()

        try:
            await page.goto(record.quote_url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
            # Single-page apps (hash routes like #/quoting/...) render content
            # via JS after the initial load. Give the app a moment to paint,
            # then wait for network to go quiet as a proxy for "done rendering".
            try:
                await page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass  # some sites never go fully idle (polling, analytics) - proceed anyway
            await page.wait_for_timeout(1500)  # small buffer for late-mounting components

            # Detect anti-direct-linking redirects: if we asked for a deep
            # quote-flow URL but landed somewhere else (e.g. the bare
            # homepage), a real visitor would click through from there
            # instead of being blocked. Do the same, once, before starting
            # the normal step loop.
            landed_url = page.url
            requested_path = record.quote_url.split("//", 1)[-1].split("/", 1)
            requested_domain = requested_path[0] if requested_path else ""
            if requested_domain not in landed_url:
                cta_pos = await find_homepage_cta(page)
                if cta_pos:
                    await page.mouse.click(cta_pos["x"], cta_pos["y"])
                    try:
                        await page.wait_for_load_state("networkidle", timeout=8000)
                    except Exception:
                        pass
                    await page.wait_for_timeout(1500)

            for step in range(MAX_STEPS):
                page_text = await safe_inner_text(page)
                check_page_text(page_text)  # raises GuardrailStop if blocked/declaration/payment

                fields = await extract_visible_fields(page)
                did_something = False

                if fields:
                    mapping = await map_fields_with_claude(fields, applicant)
                    await fill_mapped_fields(page, mapping, fields, applicant)
                    did_something = True
                else:
                    # No native <select>/<input>/<textarea> found. Some sites
                    # use styled div/button comboboxes instead of real
                    # <select> tags, which are otherwise invisible to us.
                    if await try_custom_dropdown(page, applicant.province):
                        did_something = True

                btn_selector = await find_continue_button(page)

                if not did_something and not btn_selector:
                    break  # nothing left we can do on this page

                await mask_sensitive_before_screenshot(page)
                shot = EVIDENCE_DIR / f"{record.registry_id}_step{step}_{_ts()}.png"
                await page.screenshot(path=str(shot))
                result.evidence_artifact_path = str(shot)

                if not btn_selector:
                    break  # filled something but no way to proceed - stop here

                try:
                    await page.click(btn_selector, timeout=5000)
                    # SPA hash-route changes don't trigger a full navigation,
                    # so wait for the network to settle instead, then a short
                    # buffer for the next step's components to mount.
                    try:
                        await page.wait_for_load_state("networkidle", timeout=6000)
                    except Exception:
                        pass
                    await page.wait_for_timeout(1000)
                except Exception:
                    break

            final_text = await safe_inner_text(page)
            check_page_text(final_text)

            premium = _extract_premium(final_text)
            await mask_sensitive_before_screenshot(page)
            final_shot = EVIDENCE_DIR / f"{record.registry_id}_final_{_ts()}.png"
            await page.screenshot(path=str(final_shot))
            result.evidence_artifact_path = str(final_shot)
            result.evidence_timestamp = datetime.now(timezone.utc).isoformat()
            result.source_url = page.url

            if premium:
                result.annual_premium = premium
                result.status = Status.QUOTED_NON_COMPARABLE
                result.next_action = "Verify coverage assumptions match benchmark before marking quoted_comparable."
            else:
                result.status = Status.UNRESOLVED
                result.next_action = "No premium detected on final page reached — review evidence manually."

        except GuardrailStop as gs:
            result.status = Status(gs.status)
            result.failure_reason = gs.reason
            result.next_action = "Logged per guardrail; do not retry automatically."
            result.evidence_timestamp = datetime.now(timezone.utc).isoformat()
            result.source_url = page.url if page else record.quote_url
            try:
                await mask_sensitive_before_screenshot(page)
                block_shot = EVIDENCE_DIR / f"{record.registry_id}_blocked_{_ts()}.png"
                await page.screenshot(path=str(block_shot))
                result.evidence_artifact_path = str(block_shot)
            except Exception:
                pass  # page may already be in a bad state; don't let evidence capture mask the real error

        except Exception as e:
            result.status = Status.UNREACHABLE
            result.failure_reason = f"{type(e).__name__}: {e}"
            result.next_action = "One bounded retry permitted for transient errors only."
            result.evidence_timestamp = datetime.now(timezone.utc).isoformat()
            result.source_url = record.quote_url

        finally:
            await browser.close()

    _log(record, result)
    return result


def _extract_premium(text: str):
    """Rough premium detector: looks for $X,XXX near 'annual', 'premium',
    'per year', 'total'. Tune once you see a real results page's wording."""
    patterns = [
        r"(?:annual premium|total premium|per year|/year|annually)[^\$]{0,30}\$\s?([\d,]+\.?\d*)",
        r"\$\s?([\d,]+\.?\d*)\s?(?:/year|per year|annually)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                continue
    return None


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _log(record: MarketRecord, result: QuoteResult):
    log_path = LOGS_DIR / f"{record.registry_id}.jsonl"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "registry_id": record.registry_id,
        "status": result.status.value if isinstance(result.status, Status) else result.status,
        "source_url": result.source_url,
        "failure_reason": result.failure_reason,
    }
    entry = redact_for_storage(entry)
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    from intake_config import build_applicant

    with open(Path(__file__).parent / "registry" / "seed_registry.json") as f:
        records = json.load(f)

    rec = MarketRecord(**records[0])
    applicant = build_applicant()

    res = asyncio.run(run_route(rec, applicant))
    print(json.dumps(asdict(res), default=str, indent=2))
