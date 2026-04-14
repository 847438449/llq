from __future__ import annotations

import pytest

from app.browser.tools import extract_page_context


class BadLocator:
    async def inner_text(self, timeout=5000):
        raise RuntimeError("cannot read body")


class FakePage:
    url = "https://example.com"

    async def title(self):
        return "Example"

    async def goto(self, *args, **kwargs):
        return None

    def locator(self, _):
        return BadLocator()

    async def evaluate(self, _):
        return {"buttons": [], "links": [], "inputs": []}


@pytest.mark.asyncio
async def test_extract_page_context_partial_on_body_failure() -> None:
    ctx = await extract_page_context(FakePage())
    assert ctx["title"] == "Example"
    assert ctx["summary"] == ""
    assert "warning" in ctx and ctx["warning"]
