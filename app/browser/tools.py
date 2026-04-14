from __future__ import annotations

import asyncio
import inspect
from pathlib import Path

from app.browser.manager import SyncPageWrapper
from playwright.async_api import Page


def _is_async_page(page) -> bool:
    if isinstance(page, SyncPageWrapper):
        return False
    return inspect.iscoroutinefunction(getattr(page, "goto", None))


async def _run_sync_page(wrapper: SyncPageWrapper, fn):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(wrapper.executor, fn)


async def open_url(page: Page | SyncPageWrapper, url: str) -> dict:
    if _is_async_page(page):
        await page.goto(url, wait_until="domcontentloaded")
        return {"title": await page.title()}

    await _run_sync_page(page, lambda: page.page.goto(url, wait_until="domcontentloaded"))
    title = await _run_sync_page(page, lambda: page.page.title())
    return {"title": title}


async def search_text(page: Page | SyncPageWrapper, text: str) -> dict:
    content = await page.content() if _is_async_page(page) else await _run_sync_page(page, lambda: page.page.content())
    return {"query": text, "found": text.lower() in content.lower()}


async def click_text(page: Page | SyncPageWrapper, text: str) -> dict:
    if _is_async_page(page):
        await page.get_by_text(text).first.click(timeout=5000)
    else:
        await _run_sync_page(page, lambda: page.page.get_by_text(text).first.click(timeout=5000))
    return {"clicked_text": text}


async def extract_page_summary(page: Page | SyncPageWrapper, max_chars: int = 400) -> dict:
    if _is_async_page(page):
        title = await page.title()
        body_text = await page.locator("body").inner_text(timeout=5000)
    else:
        title = await _run_sync_page(page, lambda: page.page.title())
        body_text = await _run_sync_page(page, lambda: page.page.locator("body").inner_text(timeout=5000))
    return {"title": title, "summary": " ".join(body_text.split())[:max_chars]}


async def extract_page_context(page: Page | SyncPageWrapper) -> dict:
    if _is_async_page(page):
        title = await page.title()
        url = page.url or "about:blank"
        try:
            body_text = await page.locator("body").inner_text(timeout=5000)
            summary, warning = " ".join(body_text.split())[:1000], None
        except Exception as exc:
            summary, warning = "", f"body_extract_failed: {exc}"
        context = await page.evaluate(_CONTEXT_JS)
    else:
        title = await _run_sync_page(page, lambda: page.page.title())
        url = page.url or "about:blank"
        try:
            body_text = await _run_sync_page(page, lambda: page.page.locator("body").inner_text(timeout=5000))
            summary, warning = " ".join(body_text.split())[:1000], None
        except Exception as exc:
            summary, warning = "", f"body_extract_failed: {exc}"
        context = await _run_sync_page(page, lambda: page.page.evaluate(_CONTEXT_JS))

    return {
        "url": url,
        "title": title,
        "buttons": context.get("buttons", []),
        "links": context.get("links", []),
        "inputs": context.get("inputs", []),
        "summary": summary,
        "warning": warning,
    }


async def take_screenshot(page: Page | SyncPageWrapper, path: Path, timeout_ms: int = 10000, full_page: bool = False) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    if _is_async_page(page):
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(path), full_page=full_page, timeout=timeout_ms)
    else:
        await _run_sync_page(page, lambda: page.page.wait_for_load_state("domcontentloaded"))
        await _run_sync_page(page, lambda: page.page.wait_for_timeout(500))
        await _run_sync_page(page, lambda: page.page.screenshot(path=str(path), full_page=full_page, timeout=timeout_ms))
    return {"path": str(path)}


_CONTEXT_JS = """
() => {
  const isVisible = (el) => {
    if (!el) return false;
    const style = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return style && style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
  };
  const buttons = Array.from(document.querySelectorAll('button,[role="button"],input[type="button"],input[type="submit"]'))
    .filter(isVisible).slice(0, 10)
    .map((el) => (el.innerText || el.value || el.getAttribute('aria-label') || '').trim())
    .filter(Boolean);
  const links = Array.from(document.querySelectorAll('a[href]')).filter(isVisible).slice(0, 10)
    .map((el) => ({ text: (el.innerText || el.getAttribute('aria-label') || '').trim(), href: el.href }));
  const inputs = Array.from(document.querySelectorAll('input, textarea, select')).filter(isVisible).slice(0, 10)
    .map((el) => ({ type: el.getAttribute('type') || el.tagName.toLowerCase(), placeholder: el.getAttribute('placeholder') || '', name: el.getAttribute('name') || '' }));
  return { buttons, links, inputs };
}
"""
