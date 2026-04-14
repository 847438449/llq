from __future__ import annotations

from app.memory.store import MemoryStore
from app.skills.registry import SkillRegistry


def test_skill_registry_matching() -> None:
    registry = SkillRegistry()
    assert registry.match("https://github.com/openai/openai-python").name == "github"
    assert registry.match("https://www.google.com/search?q=test").name == "google"
    assert registry.match("https://example.org").name == "generic_web"


def test_memory_retrieval_and_summarization(tmp_path) -> None:
    store = MemoryStore(path=str(tmp_path / "tasks.json"))
    store.save_task_record(
        {
            "task_id": "1",
            "user_input": "find repo",
            "domain": "github.com",
            "visited_urls": ["https://github.com"],
            "successful_actions": [{"action": "click_text", "params": {"text": "Issues"}}],
            "failed_actions": [],
            "matched_skill": "github",
            "final_extracted_summary": "ok",
        }
    )

    patterns = store.recent_success_patterns("github.com")
    assert patterns
    summary = store.summarize_patterns("github.com")
    assert "click_text" in summary
