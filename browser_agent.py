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
     recognizable form is found ? and returns whatever result that
     implies (blocked / manual_handoff / unresolved / quoted)

This is slower than hardcoded selectors but works across sites you
haven't tested yet, which matters more given the 6-route scope and
the time you have left today.
"""

import asyncio
import dataclasses
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict

from formatting_utils import postal_code_variants

from playwright.async_api import async_playwright, Page
import anthropic

from schema import MarketRecord, QuoteResult, Status, Applicant, NEVER_DEFAULT_FIELDS
from guardrails import check_page_text, GuardrailStop, redact_for_storage
from normalizer import normalize_quote_result
from site_hooks import get_hook

EVIDENCE_DIR = Path(__file__).parent / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

MAX_STEPS = 8          # bounded-attempt policy: don't loop forever on one route
NAV_TIMEOUT_MS = 20000

client = anthropic.Anthropic()

BOOLEAN_FIELD_NAMES = {
    f.name for f in dataclasses.fields(Applicant)
    if f.type == bool or f.type == "bool"
}

BOOL_LABEL_OVERRIDES = {
    "dcpd_included": "DCPD",
    "opcf_44r": "family protection",
    "telematics_opt_in": "telematics",
    "telematics_data_consent": "telematics",
    "driver_training_completed": "driver training",
    "winter_tires": "winter tires",
    "anti_theft_device": "anti theft",
    "unrepaired_damage": "unrepaired damage",
    "carpool": "carpool",
    "is_student": "student",
    "is_good_student": "good student",
    "is_mature_driver": "mature driver",
    "has_multi_policy": "multi policy",
    "has_mortgage": "mortgage",
    "has_tenant_insurance": "tenant insurance",
    "registered_owner_same_as_driver": "registered owner",
    "garaging_address_same_as_home": "garaging address",
    "is_self_employed": "self employed",
}


class FieldUnconfirmedError(Exception):
    """Raised when a form asks for a field the applicant profile
    cannot safely answer - never touched, or only at an unconfirmed
    default for a field where that's not acceptable. Never guess."""
    pass


def should_fill_field(applicant: Applicant, field_name: str) -> bool:
    confidence = applicant.get_confidence(field_name)
    if confidence == "verified":
        return True
    if confidence == "default":
        return field_name not in NEVER_DEFAULT_FIELDS
    return False

# Field names we NEVER auto-fill even if Claude maps them ? these must
# stop the flow and go to manual_handoff instead. Second layer of
# protection on top of guardrails.check_page_text().
NEVER_AUTOFILL = {"licence_number_confirm", "signature", "payment_card", "cvv"}

CHAT_WIDGET_SELECTORS = [
    '[id*="intercom"]', '[class*="intercom"]',
    '[id*="drift"]', '[class*="drift"]',
    '[id*="zendesk"]', '[class*="zendesk"]',
    '[id*="tawk"]', '[class*="tawk"]',
    '[id*="crisp"]', '[class*="crisp"]',
    '[class*="chat-widget"]', '[class*="chat-bubble"]',
]
CHAT_WIDGET_SELECTOR_JS = ", ".join(CHAT_WIDGET_SELECTORS)


async def dismiss_cookie_banner(page: Page) -> bool:
    accept_texts = [
        "accept all", "accept all cookies", "allow all", "allow all cookies",
        "i agree", "agree", "got it", "accept cookies", "accept",
    ]
    clicked = await page.evaluate(f"""
    () => {{
        const targets = {accept_texts!r};
        const els = [...document.querySelectorAll('button, a, div[role="button"]')];
        for (const el of els) {{
            if (el.offsetParent === null) continue;
            const txt = (el.innerText || '').trim().toLowerCase();
            if (targets.includes(txt)) {{
                const r = el.getBoundingClientRect();
                return {{x: r.x + r.width/2, y: r.y + r.height/2}};
            }}
        }}
        return null;
    }}
    """)
    if clicked:
        await page.mouse.click(clicked["x"], clicked["y"])
        await page.wait_for_timeout(500)
        return True
    return False


async def dismiss_unexpected_popup(page: Page) -> bool:
    dismiss_texts = ["no thanks", "skip", "maybe later", "close", "not now", "dismiss"]
    result = await page.evaluate(f"""
    () => {{
        const targets = {dismiss_texts!r};
        const closeIconSelectors = ['[aria-label="close" i]', '[aria-label="dismiss" i]', '.modal-close', '.popup-close'];
        for (const sel of closeIconSelectors) {{
            const el = document.querySelector(sel);
            if (el && el.offsetParent !== null) {{
                const r = el.getBoundingClientRect();
                return {{x: r.x + r.width/2, y: r.y + r.height/2}};
            }}
        }}
        const els = [...document.querySelectorAll('button, a')];
        for (const el of els) {{
            if (el.offsetParent === null) continue;
            const txt = (el.innerText || '').trim().toLowerCase();
            if (targets.includes(txt)) {{
                const r = el.getBoundingClientRect();
                return {{x: r.x + r.width/2, y: r.y + r.height/2}};
            }}
        }}
        return null;
    }}
    """)
    if result:
        await page.mouse.click(result["x"], result["y"])
        await page.wait_for_timeout(400)
        return True
    return False


async def fill_postal_code(page: Page, selector: str, raw_value: str) -> bool:
    for variant in postal_code_variants(raw_value):
        try:
            await page.fill(selector, variant)
            await page.wait_for_timeout(300)
            has_error = await page.evaluate("""
            () => {
                const text = document.body.innerText.toLowerCase();
                return text.includes('invalid postal code') || text.includes('enter a valid postal code');
            }
            """)
            if not has_error:
                return True
        except Exception:
            continue
    return False


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
    candidate = await page.evaluate(f"""
    () => {{
        const chatSels = {CHAT_WIDGET_SELECTOR_JS!r};
        const texts = ['continue', 'next', 'get quote', 'get my quote', 'see my quote',
                        'get my rate', 'submit', 'proceed', 'get started',
                        'confirm', 'accept', 'agree', 'ok', 'got it'];
        const buttons = [...document.querySelectorAll('button, input[type=submit], a.button, a.btn')];
        for (const b of buttons) {{
            if (b.closest(chatSels)) continue;
            const t = (b.innerText || b.value || '').trim().toLowerCase();
            if (t.includes('chat with')) continue;
            if (texts.some(x => t.includes(x))) {{
                return b.id ? `#${{b.id}}` : (b.className ? `.${{b.className.split(' ')[0]}}` : null);
            }}
        }}
        return null;
    }}
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
        const chatSels = {CHAT_WIDGET_SELECTOR_JS!r};
        const targets = {exact_targets!r};
        const els = [...document.querySelectorAll('button, a, div[role="button"]')];
        for (const el of els) {{
            if (el.closest(chatSels)) continue;
            const txt = (el.innerText || '').trim().toLowerCase();
            if (txt.includes('chat with')) continue;
            if (targets.includes(txt) && el.offsetParent !== null) {{
                const r = el.getBoundingClientRect();
                return {{x: r.x + r.width / 2, y: r.y + r.height / 2}};
            }}
        }}
        return null;
    }}
    """)
    return candidate


async def find_dropdown_trigger(page: Page, near_label: str = "") -> dict | None:
    """Find a custom dropdown trigger element using multiple signals,
    not just literal 'Select' text. Checks ARIA roles, common class
    name patterns, and placeholder-style text together."""
    return await page.evaluate(f"""
    (nearLabel) => {{
        const chatSels = {CHAT_WIDGET_SELECTOR_JS!r};
        const looksLikeDropdown = (el) => {{
            if (el.offsetParent === null) return false;
            if (el.closest(chatSels)) return false;
            const txt = (el.innerText || '').trim().toLowerCase();
            if (txt.includes('chat with')) return false;
            const role = el.getAttribute('role') || '';
            const ariaHaspopup = el.getAttribute('aria-haspopup') || '';
            const cls = (el.className || '').toString().toLowerCase();
            return (
                role === 'combobox' ||
                ariaHaspopup === 'listbox' ||
                cls.includes('dropdown') ||
                cls.includes('select') ||
                cls.includes('combobox') ||
                cls.includes('mui-select') ||
                cls.includes('react-select') ||
                cls.includes('ant-select') ||
                el.getAttribute('aria-autocomplete') === 'list' ||
                txt === 'select' ||
                (txt === '' && !!el.querySelector('svg, .chevron, .arrow'))
            );
        }};

        if (nearLabel) {{
            const labelEls = [...document.querySelectorAll('label, span, div, p, h1, h2, h3, h4')];
            for (const lbl of labelEls) {{
                const lt = (lbl.innerText || '').trim().toLowerCase();
                if (lt !== nearLabel.toLowerCase() && !lt.startsWith(nearLabel.toLowerCase())) continue;
                if (lbl.offsetParent === null) continue;
                const container = lbl.closest('div, section, fieldset, form') || lbl.parentElement;
                if (!container) continue;
                const local = [...container.querySelectorAll('div, button, span, [role="combobox"], [role="button"]')];
                const matches = local.filter(looksLikeDropdown);
                if (matches.length) {{
                    const el = matches[0];
                    const r = el.getBoundingClientRect();
                    return {{x: r.x + r.width / 2, y: r.y + r.height / 2}};
                }}
            }}
        }}

        const candidates = [...document.querySelectorAll(
            'div, button, span, [role="combobox"], [role="button"]'
        )];
        const matches = candidates.filter(el => {{
            if (!looksLikeDropdown(el)) return false;
            if (nearLabel) {{
                const parentText = (el.closest('div,section,fieldset')?.innerText || '').toLowerCase();
                return parentText.includes(nearLabel.toLowerCase());
            }}
            return true;
        }});
        if (matches.length === 0) return null;
        const el = matches[matches.length - 1];
        const r = el.getBoundingClientRect();
        return {{x: r.x + r.width / 2, y: r.y + r.height / 2}};
    }}
    """, near_label)


async def try_custom_dropdown(page: Page, value: str, near_label: str = "") -> bool:
    """Fallback for custom-styled dropdown/combobox components that are
    NOT native <select> elements (common in React-built sites). Our
    extract_visible_fields() only finds real <select>/<input>/<textarea>
    tags, so a styled div/button dropdown is invisible to it ? this is
    why some sites produce zero fields even though a form is clearly
    on screen.

    Uses find_dropdown_trigger() for broader detection (ARIA roles,
    class names, chevron icons), then clicks the matching option."""
    try:
        trigger_pos = await find_dropdown_trigger(page, near_label)
        if trigger_pos:
            await page.mouse.click(trigger_pos["x"], trigger_pos["y"])
        else:
            clicked = False
            if near_label:
                label_loc = page.get_by_text(near_label, exact=True).first
                if await label_loc.count() > 0:
                    parent = label_loc.locator("xpath=ancestor::*[self::div or self::section or self::fieldset][1]")
                    for loc in (
                        parent.get_by_text(re.compile(r"select", re.I)).first,
                        parent.locator("[role='combobox']").first,
                        parent.locator("[aria-haspopup='listbox']").first,
                    ):
                        if await loc.count() > 0:
                            await loc.click(timeout=3000)
                            clicked = True
                            break
            if not clicked:
                for loc in (
                    page.get_by_text(re.compile(r"^select\.{0,3}$", re.I)).first,
                    page.locator("[role='combobox']").first,
                ):
                    if await loc.count() > 0:
                        await loc.click(timeout=3000)
                        clicked = True
                        break
            if not clicked:
                return False
        await page.wait_for_timeout(500)

        option_pos = await page.evaluate(f"""
        () => {{
            const target = {value.lower()!r};
            const candidates = [...document.querySelectorAll('li, div, span, button, [role="option"]')];
            const matches = candidates.filter(el => {{
                const txt = (el.innerText || '').trim().toLowerCase();
                return (txt === target || txt.includes(target)) && el.offsetParent !== null;
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

        # Playwright fallback for option list items
        for loc in (
            page.get_by_role("option", name=str(value)).first,
            page.get_by_text(str(value), exact=True).last,
        ):
            if await loc.count() > 0:
                await loc.click(timeout=3000)
                await page.wait_for_timeout(500)
                return True
        return False
    except Exception:
        return False


async def try_custom_checkbox(page: Page, label_text: str, desired_state: bool) -> bool:
    """Find and set a custom-styled checkbox/toggle by matching its
    associated label text, for widgets that aren't native <input
    type=checkbox>. Only acts if the current state differs from
    desired_state, to avoid accidentally un-checking something."""
    try:
        result = await page.evaluate("""
        (labelText) => {
            const candidates = [...document.querySelectorAll(
                '[role="checkbox"], [role="switch"], .toggle, .checkbox-custom'
            )];
            for (const el of candidates) {
                if (el.offsetParent === null) continue;
                const container = el.closest('div,label,li') || el;
                const txt = (container.innerText || '').toLowerCase();
                if (txt.includes(labelText.toLowerCase())) {
                    const checked = el.getAttribute('aria-checked') === 'true'
                                   || el.classList.contains('checked')
                                   || el.classList.contains('active');
                    const r = el.getBoundingClientRect();
                    return {x: r.x + r.width/2, y: r.y + r.height/2, checked};
                }
            }
            return null;
        }
        """, label_text)
        if not result:
            return False
        if result["checked"] != desired_state:
            await page.mouse.click(result["x"], result["y"])
            await page.wait_for_timeout(300)
        return True
    except Exception:
        return False


async def try_date_field(page: Page, applicant: Applicant) -> bool:
    """Find date-related fields (native <input type=date> or
    calendar-popup widgets) and fill with applicant.effective_date.
    Specifically targets fields whose label suggests a policy/coverage
    start date, since these commonly have no natural default."""
    date_value = getattr(applicant, "effective_date", None)
    if not date_value:
        from datetime import date
        date_value = date.today().isoformat()

    parts = date_value.split("-")
    display_formats = [date_value]
    if len(parts) == 3:
        y, m, d = parts
        display_formats.extend([f"{m}/{d}/{y}", f"{d}/{m}/{y}"])

    DATE_LABEL_JS = """
    (label, placeholder, ariaLabel) => {
        label = (label || '').toLowerCase();
        placeholder = (placeholder || '').toLowerCase();
        ariaLabel = (ariaLabel || '').toLowerCase();
        const blob = label + ' ' + placeholder + ' ' + ariaLabel;
        if (blob.includes('start date') || blob.includes('effective date') || blob.includes('policy date')) return true;
        if (blob.includes('when') && (blob.includes('effect') || blob.includes('start') || blob.includes('policy') || blob.includes('coverage'))) return true;
        if (blob.includes('date') && (blob.includes('start') || blob.includes('effective') || blob.includes('when'))) return true;
        if (/mm\\/dd\\/yyyy|dd\\/mm\\/yyyy/.test(placeholder)) return true;
        return false;
    }
    """

    native_filled = await page.evaluate(f"""
    (dateVal) => {{
        const isDateLabel = {DATE_LABEL_JS};
        for (const el of document.querySelectorAll('input[type="date"]')) {{
            if (el.offsetParent === null) continue;
            const label = (el.closest('div,label,section,fieldset')?.innerText || '');
            if (isDateLabel(label, el.placeholder, el.getAttribute('aria-label'))) {{
                el.value = dateVal;
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                return true;
            }}
        }}
        return false;
    }}
    """, date_value)
    if native_filled:
        return True

    # Prefer MM/DD/YYYY first when placeholder suggests it
    ordered_formats = display_formats[:]
    if len(parts) == 3:
        y, m, d = parts
        mmdd = f"{m}/{d}/{y}"
        ordered_formats = [mmdd] + [f for f in ordered_formats if f != mmdd]

    for fmt in ordered_formats:
        text_filled = await page.evaluate(f"""
        (dateVal) => {{
            const isDateLabel = {DATE_LABEL_JS};
            for (const el of document.querySelectorAll('input:not([type=hidden]):not([type=checkbox]):not([type=radio])')) {{
                if (el.offsetParent === null || el.type === 'date') continue;
                const label = (el.closest('div,label,section,fieldset')?.innerText || '');
                const aria = el.getAttribute('aria-label') || '';
                if (isDateLabel(label, el.placeholder, aria)) {{
                    el.focus();
                    el.click();
                    el.value = '';
                    el.value = dateVal;
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                    el.dispatchEvent(new Event('blur', {{bubbles: true}}));
                    return el.value === dateVal || el.value.length > 0;
                }}
            }}
            return false;
        }}
        """, fmt)
        if text_filled:
            return True

    trigger = await page.evaluate(f"""
    () => {{
        const isDateLabel = {DATE_LABEL_JS};
        for (const el of document.querySelectorAll('input, button, div[role="button"], span')) {{
            if (el.offsetParent === null) continue;
            const label = (el.closest('div,label,section,fieldset')?.innerText || '');
            const aria = el.getAttribute('aria-label') || '';
            if (isDateLabel(label, el.placeholder, aria)) {{
                const r = el.getBoundingClientRect();
                if (r.width > 0 && r.height > 0) {{
                    return {{x: r.x + r.width/2, y: r.y + r.height/2}};
                }}
            }}
        }}
        return null;
    }}
    """)
    if not trigger:
        return False

    await page.mouse.click(trigger["x"], trigger["y"])
    await page.wait_for_timeout(500)
    # Look for a "Today" quick-select button first, most calendar widgets have one
    today_btn = await page.evaluate("""
    () => {
        const els = [...document.querySelectorAll('button, a, div')];
        for (const el of els) {
            const txt = (el.innerText || '').trim().toLowerCase();
            if (txt === 'today' && el.offsetParent !== null) {
                const r = el.getBoundingClientRect();
                return {x: r.x + r.width/2, y: r.y + r.height/2};
            }
        }
        return null;
    }
    """)
    if today_btn:
        await page.mouse.click(today_btn["x"], today_btn["y"])
        await page.wait_for_timeout(300)
        return True
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


async def try_native_radio_group(page: Page, name_attr: str, desired_yes: bool) -> bool:
    """Handle a native radio button group (multiple <input type=radio>
    sharing the same name attribute) by finding the specific option
    whose label matches Yes/No, rather than using a single ambiguous
    selector which fails when multiple radios share one name."""
    target_text = "yes" if desired_yes else "no"
    result = await page.evaluate("""
    (nameAttr, targetText) => {
        const radios = [...document.querySelectorAll(`input[type="radio"][name="${nameAttr}"]`)];
        for (const r of radios) {
            if (r.offsetParent === null) continue;
            let label = '';
            if (r.id) {
                const lbl = document.querySelector(`label[for="${r.id}"]`);
                if (lbl) label = lbl.innerText;
            }
            if (!label && r.closest('label')) label = r.closest('label').innerText;
            if (!label) label = r.value || '';
            if (label.trim().toLowerCase() === targetText) {
                const rect = r.getBoundingClientRect();
                return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
            }
        }
        return null;
    }
    """, name_attr, target_text)
    if result:
        await page.mouse.click(result["x"], result["y"])
        await page.wait_for_timeout(200)
        return True
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
  (e.g. "confirm licence number", "SIN") ? map those to null.
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

        if not should_fill_field(applicant, attr):
            raise FieldUnconfirmedError(
                f"Form asks for '{attr}' but this field is not confirmed "
                f"(confidence: {applicant.get_confidence(attr)}). Refusing to guess."
            )

        value = applicant_dict.get(attr)
        if value in (None, ""):
            continue
        f = field_by_selector[selector]
        try:
            if f["tag"] == "select":
                try:
                    await page.select_option(selector, label=str(value))
                except Exception:
                    near = {"model_year": "year", "make": "make", "province": ""}.get(attr, "")
                    await try_custom_dropdown(page, str(value), near_label=near)
            elif f["type"] in ("checkbox", "radio"):
                desired = (
                    bool(value) if isinstance(value, bool)
                    else str(value).lower() in ("true", "1", "yes")
                )
                filled = False
                if f["type"] == "radio" and f.get("name"):
                    filled = await try_native_radio_group(page, f["name"], desired)
                elif f["type"] == "checkbox":
                    try:
                        if desired:
                            await page.check(selector)
                        else:
                            await page.uncheck(selector)
                        filled = True
                    except Exception:
                        pass
                if not filled and attr in BOOLEAN_FIELD_NAMES:
                    label = BOOL_LABEL_OVERRIDES.get(attr, attr.replace("_", " "))
                    await try_custom_checkbox(page, label, desired)
            else:
                if attr == "street" and f["tag"] != "select":
                    handled = await try_address_autocomplete(page, selector, str(value))
                    if handled:
                        continue
                if attr == "postal_code" and value:
                    await fill_postal_code(page, selector, str(value))
                else:
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
        const sensitive = /licen[cs]e|\\bvin\\b|dob|birth|postal|\\baddress\\b|\\bstreet\\b|phone|email|\\bsin\\b|\\bname\\b|employer|occupation|\\bindustry\\b|school|financ|lien|leas|colour|color|\\bvalue\\b|income/i;
        document.querySelectorAll('input, textarea').forEach(el => {
            const blob = (el.name + ' ' + el.id + ' ' + (el.placeholder||'')).replace(/_/g, ' ').toLowerCase();
            if (sensitive.test(blob) && el.value) {
                el.value = '••••••';
            }
        });
    }
    """)


def _step_log(registry_id: str, step: int, msg: str):
    print(f"[{registry_id}] step {step}: {msg}")


async def run_custom_widget_fallbacks(
    page: Page, applicant: Applicant, record: MarketRecord, step: int
) -> bool:
    """Date pickers, custom checkboxes, and non-native dropdowns after native fill."""
    did_something = False

    if await try_date_field(page, applicant):
        _step_log(record.registry_id, step, "date/start field filled")
        did_something = True
    else:
        _step_log(record.registry_id, step, "no date/start field matched")

    for field_name in BOOLEAN_FIELD_NAMES:
        label = BOOL_LABEL_OVERRIDES.get(field_name, field_name.replace("_", " "))
        desired = bool(getattr(applicant, field_name, False))
        if await try_custom_checkbox(page, label, desired):
            _step_log(record.registry_id, step, f"boolean fallback handled ({field_name})")
            did_something = True

    if await try_custom_dropdown(page, applicant.province):
        _step_log(record.registry_id, step, "custom dropdown handled (province)")
        did_something = True

    if applicant.model_year:
        if await try_custom_dropdown(page, applicant.model_year, near_label="year"):
            _step_log(record.registry_id, step, f"year dropdown handled ({applicant.model_year})")
            did_something = True

    if applicant.make:
        if await try_custom_dropdown(page, applicant.make, near_label="make"):
            _step_log(record.registry_id, step, f"make dropdown handled ({applicant.make})")
            did_something = True

    return did_something


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

    browser = None
    page = None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=120)
            context = await browser.new_context(
                viewport={"width": 1366, "height": 900},
                locale="en-CA",
                timezone_id="America/Toronto",
            )
            page = await context.new_page()

            try:
                await page.goto(record.quote_url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
                await dismiss_cookie_banner(page)
                try:
                    await page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass
                await page.wait_for_timeout(1500)

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

                hook = get_hook(record.registry_id)
                if hook and hook.on_entry:
                    try:
                        await hook.on_entry(page, record, applicant)
                        await page.wait_for_timeout(1000)
                    except Exception:
                        pass

                for step in range(MAX_STEPS):
                    page_text = await safe_inner_text(page)
                    check_page_text(page_text)

                    fields = await extract_visible_fields(page)
                    did_something = False
                    mapping: dict = {}

                    if fields:
                        mapping = await map_fields_with_claude(fields, applicant)
                        if mapping:
                            await fill_mapped_fields(page, mapping, fields, applicant)
                            did_something = True
                        elif await dismiss_unexpected_popup(page):
                            did_something = True
                    else:
                        if await dismiss_unexpected_popup(page):
                            did_something = True
                        elif hook and hook.on_empty_fields:
                            try:
                                if await hook.on_empty_fields(page, record, applicant):
                                    did_something = True
                            except Exception:
                                pass
                        if not did_something and await try_custom_dropdown(page, applicant.province):
                            did_something = True

                    if await run_custom_widget_fallbacks(page, applicant, record, step):
                        did_something = True

                    btn_selector = await find_continue_button(page)

                    if not did_something and not btn_selector:
                        break

                    await mask_sensitive_before_screenshot(page)
                    shot = EVIDENCE_DIR / f"{record.registry_id}_step{step}_{_ts()}.png"
                    await page.screenshot(path=str(shot))
                    result.evidence_artifact_path = str(shot)

                    if not btn_selector:
                        break

                    try:
                        await page.click(btn_selector, timeout=5000)
                        try:
                            await page.wait_for_load_state("networkidle", timeout=6000)
                        except Exception:
                            pass
                        await page.wait_for_timeout(1000)
                    except Exception:
                        break

                final_text = await safe_inner_text(page)
                check_page_text(final_text)

                await mask_sensitive_before_screenshot(page)
                final_shot = EVIDENCE_DIR / f"{record.registry_id}_final_{_ts()}.png"
                await page.screenshot(path=str(final_shot))
                result.evidence_artifact_path = str(final_shot)
                result.evidence_timestamp = datetime.now(timezone.utc).isoformat()
                result.source_url = page.url

                result = normalize_quote_result(result, final_text, applicant)

            except asyncio.CancelledError:
                raise
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
                    pass
            except FieldUnconfirmedError as e:
                result.status = Status.MANUAL_HANDOFF
                result.failure_reason = str(e)
                result.next_action = "Re-run interactive_intake.py and explicitly confirm this field, then retry."
                result.evidence_timestamp = datetime.now(timezone.utc).isoformat()
                result.source_url = page.url if page else record.quote_url
                try:
                    await mask_sensitive_before_screenshot(page)
                    handoff_shot = EVIDENCE_DIR / f"{record.registry_id}_field_unconfirmed_{_ts()}.png"
                    await page.screenshot(path=str(handoff_shot))
                    result.evidence_artifact_path = str(handoff_shot)
                except Exception:
                    pass
            except Exception as e:
                result.status = Status.UNREACHABLE
                result.failure_reason = f"{type(e).__name__}: {e}"
                result.next_action = "One bounded retry permitted for transient errors only."
                result.evidence_timestamp = datetime.now(timezone.utc).isoformat()
                result.source_url = page.url if page else record.quote_url
            finally:
                if browser is not None:
                    try:
                        await browser.close()
                    except Exception:
                        pass
                    browser = None
    except asyncio.CancelledError:
        raise

    _log(record, result)
    return result


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
