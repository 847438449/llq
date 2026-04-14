from __future__ import annotations

from app.skills.base import Skill


generic_web = Skill(
    name="generic_web",
    hints=[
        "Use visible links/buttons first.",
        "Prefer extract_page_summary when uncertain.",
    ],
)

bilibili = Skill(
    name="bilibili",
    domains=["bilibili.com"],
    hints=[
        "Videos often require clicking cards or tabs before details are visible.",
        "Use search_text to verify title/channel cues before clicking.",
    ],
    preferred_selectors=["a", "button", "[data-key]"],
)

github = Skill(
    name="github",
    domains=["github.com"],
    hints=[
        "Repository pages expose useful links like Issues, Pull requests, and README content.",
        "Prefer link/button text interactions over deep selectors.",
    ],
    preferred_selectors=["a[href]", "button", "summary"],
)

google = Skill(
    name="google",
    domains=["google.com"],
    hints=[
        "Search result pages contain many links; choose concise click_text targets.",
        "Use search_text to verify terms before click_text.",
    ],
    preferred_selectors=["textarea[name='q']", "a h3", "a[href]"],
)

BUILTIN_SKILLS = [bilibili, github, google, generic_web]
