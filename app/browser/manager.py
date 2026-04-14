from __future__ import annotations

from pathlib import Path
from typing import Any

from app.runtime import configure_windows_event_loop_policy, log_startup_diagnostics

configure_windows_event_loop_policy()


class BrowserManager:
    def __init__(self, screenshots_dir: str = "artifacts/screenshots") -> None:
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self._sync_playwright = None
        self._sync_browser = None
        self._sync_context = None
        self._page: Any | None = None

    async def start(self):
        from playwright.sync_api import sync_playwright

        configure_windows_event_loop_policy()
        log_startup_diagnostics("browser.start")
        self._sync_playwright = sync_playwright().start()
        self._sync_browser = self._sync_playwright.chromium.launch(headless=False)
        self._sync_context = self._sync_browser.new_context()
        self._page = self._sync_context.new_page()
        return self._page

    @property
    def page(self):
        if self._page is None:
            raise RuntimeError("Browser has not been started")
        return self._page

    async def close(self) -> None:
        if self._sync_context:
            self._sync_context.close()
        if self._sync_browser:
            self._sync_browser.close()
        if self._sync_playwright:
            self._sync_playwright.stop()
