from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from app.runtime import configure_windows_event_loop_policy, log_startup_diagnostics

configure_windows_event_loop_policy()

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright


class BrowserManager:
    def __init__(self, screenshots_dir: str = "artifacts/screenshots") -> None:
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | Any | None = None

        self._sync_playwright = None
        self._sync_browser = None
        self._sync_context = None
        self._use_sync = sys.platform == "win32"

    async def start(self) -> Page | Any:
        configure_windows_event_loop_policy()
        log_startup_diagnostics("browser.start")

        if self._use_sync:
            await asyncio.to_thread(self._start_sync)
            return self._page

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=False)
        self._context = await self._browser.new_context()
        self._page = await self._context.new_page()
        return self._page

    def _start_sync(self) -> None:
        from playwright.sync_api import sync_playwright

        self._sync_playwright = sync_playwright().start()
        self._sync_browser = self._sync_playwright.chromium.launch(headless=False)
        self._sync_context = self._sync_browser.new_context()
        self._page = self._sync_context.new_page()

    @property
    def page(self) -> Page | Any:
        if self._page is None:
            raise RuntimeError("Browser has not been started")
        return self._page

    async def close(self) -> None:
        if self._use_sync:
            await asyncio.to_thread(self._close_sync)
            return

        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    def _close_sync(self) -> None:
        if self._sync_context:
            self._sync_context.close()
        if self._sync_browser:
            self._sync_browser.close()
        if self._sync_playwright:
            self._sync_playwright.stop()
