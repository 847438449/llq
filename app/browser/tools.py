from __future__ import annotations

from pathlib import Path

from playwright.async_api import Page


async def open_url(page: Page, url: str) -> dict:
    await page.goto(url, wait_until="domcontentloaded")
    return {"title": await page.title()}


async def search_text(page: Page, text: str) -> dict:
    content = await page.content()
    found = text.lower() in content.lower()
    return {"query": text, "found": found}


async def click_text(page: Page, text: str) -> dict:
    locator = page.get_by_text(text).first
    await locator.click(timeout=5000)
    return {"clicked_text": text}


async def extract_page_summary(page: Page, max_chars: int = 400) -> dict:
    title = await page.title()
    body_text = await page.locator("body").inner_text(timeout=5000)
    summary = " ".join(body_text.split())[:max_chars]
    return {"title": title, "summary": summary}


async def extract_page_context(page: Page) -> dict:
    title = await page.title()
    url = page.url or "about:blank"

    warning: str | None = None
    try:
        body_text = await page.locator("body").inner_text(timeout=5000)
        summary = " ".join(body_text.split())[:1000]
    except Exception as exc:
        summary = ""
        warning = f"body_extract_failed: {exc}"

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

    return {
        "url": url,
        "title": title,
        "buttons": context.get("buttons", []),
        "links": context.get("links", []),
        "inputs": context.get("inputs", []),
        "summary": summary,
        "warning": warning,
    }


async def take_screenshot(page: Page, path: Path, timeout_ms: int = 10000, full_page: bool = False) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_timeout(500)
    await page.screenshot(path=str(path), full_page=full_page, timeout=timeout_ms)
    return {"path": str(path)}
