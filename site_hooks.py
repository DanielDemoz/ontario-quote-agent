"""
Per-route automation hooks for sites where generic field extraction
is not enough (SPAs, custom dropdowns, anti-direct-link redirects).

Hooks are honest site-specific navigation — not bot-detection evasion.
Each hook documents what a human visitor would do on that page.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Awaitable, Callable

from playwright.async_api import Page

from schema import Applicant, MarketRecord


@dataclass
class SiteHook:
    registry_id: str
    # Run once after initial page load (before the step loop).
    on_entry: Callable[[Page, MarketRecord, Applicant], Awaitable[bool]] | None = None
    # Run at the start of each step when no native fields were found.
    on_empty_fields: Callable[[Page, MarketRecord, Applicant], Awaitable[bool]] | None = None
    notes: str = ""


async def _click_text_option(page: Page, labels: list[str]) -> bool:
    """Click the first visible element whose trimmed text matches a label."""
    pos = await page.evaluate(
        """
        (labels) => {
            const targets = labels.map(l => l.toLowerCase());
            const els = [...document.querySelectorAll(
                'li, div, span, button, a, [role="option"], [role="menuitem"]'
            )];
            for (const el of els) {
                const txt = (el.innerText || '').trim().toLowerCase();
                if (!targets.includes(txt)) continue;
                if (el.offsetParent === null) continue;
                const r = el.getBoundingClientRect();
                if (r.width < 2 || r.height < 2) continue;
                return {x: r.x + r.width / 2, y: r.y + r.height / 2};
            }
            return null;
        }
        """,
        labels,
    )
    if not pos:
        return False
    await page.mouse.click(pos["x"], pos["y"])
    await page.wait_for_timeout(600)
    return True


async def _open_combobox(page: Page) -> bool:
    """Try ARIA combobox / listbox patterns before generic 'Select' text."""
    pos = await page.evaluate(
        """
        () => {
            const selectors = [
                '[role="combobox"]',
                '[aria-haspopup="listbox"]',
                '[aria-expanded="false"][role="button"]',
                'button[aria-label*="province" i]',
                'div[aria-label*="province" i]',
            ];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.offsetParent !== null) {
                    const r = el.getBoundingClientRect();
                    return {x: r.x + r.width / 2, y: r.y + r.height / 2};
                }
            }
            const placeholders = [...document.querySelectorAll('div, button, span')].filter(el => {
                const txt = (el.innerText || '').trim();
                return (txt === 'Select' || /^select\\s/i.test(txt)) && el.offsetParent !== null;
            });
            if (placeholders.length === 0) return null;
            const el = placeholders[placeholders.length - 1];
            const r = el.getBoundingClientRect();
            return {x: r.x + r.width / 2, y: r.y + r.height / 2};
        }
        """
    )
    if not pos:
        return False
    await page.mouse.click(pos["x"], pos["y"])
    await page.wait_for_timeout(500)
    return True


async def _click_button_exact(page: Page, labels: list[str]) -> bool:
    pos = await page.evaluate(
        """
        (labels) => {
            const targets = labels.map(l => l.toLowerCase());
            const els = [...document.querySelectorAll('button, a, [role="button"], input[type=submit]')];
            for (const el of els) {
                const txt = (el.innerText || el.value || '').trim().toLowerCase();
                if (!targets.includes(txt)) continue;
                if (el.offsetParent === null) continue;
                const r = el.getBoundingClientRect();
                return {x: r.x + r.width / 2, y: r.y + r.height / 2};
            }
            return null;
        }
        """,
        labels,
    )
    if not pos:
        return False
    await page.mouse.click(pos["x"], pos["y"])
    await page.wait_for_timeout(800)
    return True


async def _sonnet_select_province(page: Page, applicant: Applicant) -> bool:
    """Scope province pick to Sonnet's cookie/province modal."""
    trigger = await page.evaluate(
        """
        () => {
            const bodyText = document.body.innerText || '';
            if (!bodyText.includes('Please select your province')) return null;
            const modalRoot = [...document.querySelectorAll('div, section, dialog')].find(el => {
                const t = el.innerText || '';
                return t.includes('Please select your province') && t.includes('Select');
            });
            const scope = modalRoot || document.body;
            const candidates = [...scope.querySelectorAll('div, button, span, [role="combobox"]')];
            const selectEl = candidates.find(el => {
                const txt = (el.innerText || '').trim();
                return txt === 'Select' && el.offsetParent !== null;
            });
            if (!selectEl) return null;
            const r = selectEl.getBoundingClientRect();
            return {x: r.x + r.width / 2, y: r.y + r.height / 2};
        }
        """
    )
    if not trigger:
        return await _select_province(page, applicant)

    await page.mouse.click(trigger["x"], trigger["y"])
    await page.wait_for_timeout(700)

    province_labels = ["Ontario", applicant.province, "ON"]
    if not await _click_text_option(page, province_labels):
        return False

    return await _click_button_exact(page, ["Confirm"])


async def _select_province(page: Page, applicant: Applicant) -> bool:
    province_labels = [
        applicant.province,
        "Ontario",
        "ON",
        applicant.province[:2].upper() if len(applicant.province) >= 2 else "ON",
    ]
    if not await _open_combobox(page):
        return False
    return await _click_text_option(page, province_labels)


async def sonnet_on_entry(page: Page, record: MarketRecord, applicant: Applicant) -> bool:
    """Sonnet SPA province modal — select Ontario then Confirm."""
    if "sonnet" not in page.url.lower():
        return False
    if not await _sonnet_select_province(page, applicant):
        return False
    await page.wait_for_timeout(1000)
    return await _click_button_exact(page, ["Continue", "Get started", "Start"])


async def belair_on_entry(page: Page, record: MarketRecord, applicant: Applicant) -> bool:
    """belairdirect anti-direct-link: homepage CTA already handled generically."""
    return False


async def caa_on_empty_fields(page: Page, record: MarketRecord, applicant: Applicant) -> bool:
    """CAA may gate on membership — try 'continue without membership' style paths."""
    for label in ["get a quote", "start your quote", "continue", "ontario"]:
        if await _click_text_option(page, [label]):
            return True
    return await _select_province(page, applicant)


async def thinkinsure_on_empty_fields(page: Page, record: MarketRecord, applicant: Applicant) -> bool:
    for label in ["get a quote", "start quote", "compare rates", "car insurance"]:
        if await _click_text_option(page, [label]):
            return True
    return False


HOOKS: dict[str, SiteHook] = {
    "sonnet-direct-001": SiteHook(
        registry_id="sonnet-direct-001",
        on_entry=sonnet_on_entry,
        on_empty_fields=_sonnet_select_province,
        notes="Custom province modal on Sonnet SPA hash route.",
    ),
    "belairdirect-001": SiteHook(
        registry_id="belairdirect-001",
        on_entry=belair_on_entry,
        notes="Deep-link redirect handled by generic homepage CTA logic.",
    ),
    "caa-affinity-001": SiteHook(
        registry_id="caa-affinity-001",
        on_empty_fields=caa_on_empty_fields,
        notes="Affinity flow may require membership acknowledgement.",
    ),
    "thinkinsure-broker-001": SiteHook(
        registry_id="thinkinsure-broker-001",
        on_empty_fields=thinkinsure_on_empty_fields,
        notes="Broker landing page — navigate to quote/start CTA.",
    ),
}


def get_hook(registry_id: str) -> SiteHook | None:
    return HOOKS.get(registry_id)
