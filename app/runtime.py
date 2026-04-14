from __future__ import annotations

import asyncio
import logging
import platform
import sys

logger = logging.getLogger(__name__)


def configure_windows_event_loop_policy() -> None:
    """Ensure Proactor policy on Windows before Playwright startup."""
    if sys.platform != "win32":
        return

    current_policy = asyncio.get_event_loop_policy()
    if isinstance(current_policy, asyncio.WindowsProactorEventLoopPolicy):
        return

    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def log_startup_diagnostics(tag: str) -> None:
    policy_name = asyncio.get_event_loop_policy().__class__.__name__
    logger.warning(
        "[%s] python=%s executable=%s event_loop_policy=%s",
        tag,
        platform.python_version(),
        sys.executable,
        policy_name,
    )
