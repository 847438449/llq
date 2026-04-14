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
    if _is_async_page(page):
        content = await page.content()
    else:
        content = await _run_sync_page(page, lambda: page.page.content())

    found = text.lower() in content.lower()
    return {"query": text, "found": found}


async def click_text(page: Page | SyncPageWrapper, text: str) -> dict:
    if _is_async_page(page):
        locator = page.get_by_text(text).first
        await locator.click(timeout=5000)
    else:
        await _run_sync_page(page, lambda: page.page.get_by_text(text).first.click(timeout=5000))

    return {"clicked_text": text}


async def extract_page_summary(page: Page | SyncPageWrapper, max_chars: int = 400) -> dict:
    if _is_async_page(page):
        title = await page.title()
        body_text = await page.locator("body").inner_text()
    else:
        title = await _run_sync_page(page, lambda: page.page.title())
        body_text = await _run_sync_page(page, lambda: page.page.locator("body").inner_text())

    summary = " ".join(body_text.split())[:max_chars]
    return {"title": title, "summary": summary}


async def extract_page_context(page: Page | SyncPageWrapper) -> dict:
    if _is_async_page(page):
        title = await page.title()
        url = page.url or "about:blank"
        summary = await page.locator("body").inner_text()
        context = await page.evaluate(
            """
            () => {
              const isVisible = (el) => {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return style && style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
              };

              const buttons = Array.from(document.querySelectorAll('button,[role="button"],input[type="button"],input[type="submit"]'))
                .filter(isVisible)
                .slice(0, 10)
                .map((el) => (el.innerText || el.value || el.getAttribute('aria-label') || '').trim())
                .filter(Boolean);

              const links = Array.from(document.querySelectorAll('a[href]'))
                .filter(isVisible)
                .slice(0, 10)
                .map((el) => ({ text: (el.innerText || el.getAttribute('aria-label') || '').trim(), href: el.href }));

              const inputs = Array.from(document.querySelectorAll('input, textarea, select'))
                .filter(isVisible)
                .slice(0, 10)
                .map((el) => ({
                  type: el.getAttribute('type') || el.tagName.toLowerCase(),
                  placeholder: el.getAttribute('placeholder') || '',
                  name: el.getAttribute('name') || ''
                }));

              return { buttons, links, inputs };
            }
            """
        )
    else:
        title = await _run_sync_page(page, lambda: page.page.title())
        url = page.url or "about:blank"
        summary = await _run_sync_page(page, lambda: page.page.locator("body").inner_text())
        context = await _run_sync_page(
            page,
            lambda: page.page.evaluate(
                """
                () => {
                  const isVisible = (el) => {
                    if (!el) return false;
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    return style && style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
                  };

                  const buttons = Array.from(document.querySelectorAll('button,[role="button"],input[type="button"],input[type="submit"]'))
                    .filter(isVisible)
                    .slice(0, 10)
                    .map((el) => (el.innerText || el.value || el.getAttribute('aria-label') || '').trim())
                    .filter(Boolean);

                  const links = Array.from(document.querySelectorAll('a[href]'))
                    .filter(isVisible)
                    .slice(0, 10)
                    .map((el) => ({ text: (el.innerText || el.getAttribute('aria-label') || '').trim(), href: el.href }));

                  const inputs = Array.from(document.querySelectorAll('input, textarea, select'))
                    .filter(isVisible)
                    .slice(0, 10)
                    .map((el) => ({
                      type: el.getAttribute('type') || el.tagName.toLowerCase(),
                      placeholder: el.getAttribute('placeholder') || '',
                      name: el.getAttribute('name') || ''
                    }));

                  return { buttons, links, inputs };
                }
                """
            ),
        )

    short_summary = " ".join(summary.split())[:1000]
    return {
        "url": url,
        "title": title,
        "buttons": context.get("buttons", []),
        "links": context.get("links", []),
        "inputs": context.get("inputs", []),
        "summary": short_summary,
    }


async def take_screenshot(page: Page | SyncPageWrapper, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    if _is_async_page(page):
        try:
            await page.screenshot(path=str(path), full_page=True, timeout=15000)
        except Exception:
            await page.screenshot(path=str(path), full_page=False, timeout=5000)
    else:
        try:
            await _run_sync_page(page, lambda: page.page.screenshot(path=str(path), full_page=True, timeout=15000))
        except Exception:
            await _run_sync_page(page, lambda: page.page.screenshot(path=str(path), full_page=False, timeout=5000))
    return {"path": str(path)}
