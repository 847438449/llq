from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse


@dataclass
class Skill:
    name: str
    domains: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)
    preferred_selectors: list[str] = field(default_factory=list)

    def matches(self, url: str) -> bool:
        if self.name == "generic_web":
            return True
        hostname = (urlparse(url).hostname or "").lower()
        return any(hostname == domain or hostname.endswith(f".{domain}") for domain in self.domains)

    def enrich_page_state(self, page_state: dict[str, Any]) -> dict[str, Any]:
        """Hook for site-specific context extraction/shape tweaks."""
        return page_state
