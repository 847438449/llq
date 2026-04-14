from __future__ import annotations

from app.skills.base import Skill
from app.skills.builtin import BUILTIN_SKILLS, generic_web


class SkillRegistry:
    def __init__(self, skills: list[Skill] | None = None) -> None:
        self.skills = skills or BUILTIN_SKILLS

    def match(self, url: str) -> Skill:
        for skill in self.skills:
            if skill.name == "generic_web":
                continue
            if skill.matches(url):
                return skill
        return generic_web
