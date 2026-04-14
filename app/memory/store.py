from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class MemoryStore:
    def __init__(self, path: str = "artifacts/memory/tasks.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def save_task_record(self, record: dict[str, Any]) -> None:
        rows = self._load_all()
        rows.append(record)
        self.path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    def recent_success_patterns(self, domain: str, limit: int = 5) -> list[dict[str, Any]]:
        if not domain:
            return []

        rows = self._load_all()
        matched: list[dict[str, Any]] = []
        for row in reversed(rows):
            if row.get("domain") != domain:
                continue
            for action in row.get("successful_actions", []):
                matched.append(action)
                if len(matched) >= limit:
                    return matched
        return matched

    def summarize_patterns(self, domain: str, limit: int = 5) -> str:
        patterns = self.recent_success_patterns(domain, limit=limit)
        if not patterns:
            return "No relevant past experience."

        lines = []
        for item in patterns:
            action = item.get("action", "unknown")
            params = item.get("params", {})
            lines.append(f"- {action} {json.dumps(params, sort_keys=True)}")
        return "\n".join(lines)

    @staticmethod
    def domain_from_url(url: str) -> str:
        return (urlparse(url).hostname or "").lower()

    def _load_all(self) -> list[dict[str, Any]]:
        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except Exception:
            return []
