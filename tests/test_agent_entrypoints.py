"""Keep publication/recovery guidance on the pages a fresh agent reads first."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_all_agent_entrypoints_link_to_the_same_real_runbook() -> None:
    runbook = ROOT / "docs/REPOSITORY_PUBLICATION.md"
    assert runbook.is_file()
    for filename in ("AGENTS.md", "README.md", "docs/DEVELOPMENT.md", "docs/LLM_HANDOFF.md"):
        opening = "\n".join((ROOT / filename).read_text().splitlines()[:35])
        assert "REPOSITORY_PUBLICATION.md" in opening, filename


def test_interrupted_turn_recovery_has_a_root_link_and_live_state_instructions() -> None:
    agents = (ROOT / "AGENTS.md").read_text()
    runbook = (ROOT / "docs/REPOSITORY_PUBLICATION.md").read_text()
    assert "REPOSITORY_PUBLICATION.md#resuming-an-interrupted-turn" in agents
    assert "## Resuming an interrupted turn" in runbook
    section = runbook.split("## Resuming an interrupted turn", 1)[1].split("\n## ", 1)[0]
    assert "merged PRs" in section and "live" in section and "HEAD" in section
    assert "Do not repeat" in section


def test_bench_first_decision_is_discoverable_from_agent_entrypoints() -> None:
    """Keep the user's practical-engineering direction visible across fresh chats."""
    decision = ROOT / "docs/REV_A_BENCH_FIRST.md"
    assert decision.is_file()
    for filename in ("AGENTS.md", "docs/LLM_HANDOFF.md"):
        opening = "\n".join((ROOT / filename).read_text().splitlines()[:35])
        assert "REV_A_BENCH_FIRST.md" in opening, filename
