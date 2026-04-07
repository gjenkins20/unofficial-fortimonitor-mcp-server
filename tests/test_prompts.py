"""
Tests for MCP Prompt workflow templates.

Verifies that all 7 prompts are defined, have handlers, and return
properly structured PromptMessage lists.
"""

import pytest
from src.prompts.workflows import PROMPTS, PROMPT_HANDLERS


class TestPromptDefinitions:
    """Verify prompt definitions are complete and consistent."""

    def test_prompt_count(self):
        """All 7 prompts are defined."""
        assert len(PROMPTS) == 7

    def test_handler_count(self):
        """All 7 prompt handlers are defined."""
        assert len(PROMPT_HANDLERS) == 7

    def test_all_prompts_have_handlers(self):
        """Every prompt has a matching handler."""
        for name in PROMPTS:
            assert name in PROMPT_HANDLERS, f"Prompt '{name}' has no handler"

    def test_all_handlers_have_prompts(self):
        """Every handler has a matching prompt."""
        for name in PROMPT_HANDLERS:
            assert name in PROMPTS, f"Handler '{name}' has no prompt definition"

    @pytest.mark.parametrize("name", [
        "morning-situation-report",
        "investigate-outage",
        "capacity-planning-review",
        "change-impact-assessment",
        "weekly-executive-summary",
        "alert-noise-audit",
        "monitoring-coverage-check",
    ])
    def test_prompt_has_description(self, name):
        """Each prompt has a non-empty description."""
        prompt = PROMPTS[name]
        assert prompt.description
        assert len(prompt.description) > 10

    @pytest.mark.parametrize("name", [
        "morning-situation-report",
        "investigate-outage",
        "capacity-planning-review",
        "change-impact-assessment",
        "weekly-executive-summary",
        "alert-noise-audit",
        "monitoring-coverage-check",
    ])
    def test_prompt_name_matches_key(self, name):
        """Prompt name field matches the dict key."""
        prompt = PROMPTS[name]
        assert prompt.name == name


class TestPromptHandlers:
    """Verify prompt handlers produce valid messages."""

    def test_morning_report_returns_messages(self):
        messages = PROMPT_HANDLERS["morning-situation-report"]({})
        assert len(messages) >= 1
        assert messages[0].role == "user"
        assert "outage" in messages[0].content.text.lower()

    def test_investigate_outage_uses_server_id(self):
        messages = PROMPT_HANDLERS["investigate-outage"]({"server_id": "12345"})
        assert len(messages) >= 1
        assert "12345" in messages[0].content.text

    def test_capacity_review_optional_group(self):
        messages = PROMPT_HANDLERS["capacity-planning-review"]({})
        assert len(messages) >= 1
        # With group
        messages_grouped = PROMPT_HANDLERS["capacity-planning-review"]({"server_group_id": "99"})
        assert "99" in messages_grouped[0].content.text

    def test_change_impact_uses_server_id(self):
        messages = PROMPT_HANDLERS["change-impact-assessment"]({"server_id": "42"})
        assert "42" in messages[0].content.text

    def test_weekly_summary_uses_days(self):
        messages = PROMPT_HANDLERS["weekly-executive-summary"]({"days": "14"})
        assert "14" in messages[0].content.text

    def test_alert_noise_uses_days(self):
        messages = PROMPT_HANDLERS["alert-noise-audit"]({"days": "30"})
        assert "30" in messages[0].content.text

    def test_monitoring_coverage_optional_group(self):
        messages = PROMPT_HANDLERS["monitoring-coverage-check"]({})
        assert len(messages) >= 1

    def test_all_handlers_return_prompt_messages(self):
        """All handlers return lists of PromptMessage objects."""
        from mcp.types import PromptMessage
        test_args = {
            "morning-situation-report": {},
            "investigate-outage": {"server_id": "1"},
            "capacity-planning-review": {},
            "change-impact-assessment": {"server_id": "1"},
            "weekly-executive-summary": {},
            "alert-noise-audit": {},
            "monitoring-coverage-check": {},
        }
        for name, args in test_args.items():
            messages = PROMPT_HANDLERS[name](args)
            assert isinstance(messages, list), f"{name} did not return a list"
            for msg in messages:
                assert isinstance(msg, PromptMessage), f"{name} returned non-PromptMessage"
