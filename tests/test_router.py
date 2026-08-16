"""Tests for the router: agent classification, parsing, fallbacks."""
import pytest

from agents.orchestrator.router import (
    ROUTER_SYSTEM_PROMPT,
    VALID_AGENTS,
    _parse_agent_list,
)


class TestParseAgentList:
    def test_valid_list(self):
        assert _parse_agent_list('["sql"]') == ["sql"]
        assert _parse_agent_list('["sql", "web"]') == ["sql", "web"]

    def test_out_of_scope_empty_list_is_valid(self):
        assert _parse_agent_list("[]") == []

    def test_strips_json_fences(self):
        assert _parse_agent_list('```json\n["sql"]\n```') == ["sql"]

    def test_filters_unknown_agent_names(self):
        assert _parse_agent_list('["sql", "not_a_real_agent"]') == ["sql"]

    def test_empty_input_falls_back_to_all(self):
        assert _parse_agent_list("") == list(VALID_AGENTS)

    def test_malformed_json_falls_open_to_all(self):
        assert _parse_agent_list("not json at all") == list(VALID_AGENTS)
        assert _parse_agent_list('{"a": 1}') == list(VALID_AGENTS)


class TestRouterPrompt:
    def test_prompt_mentions_all_agents(self):
        for agent in VALID_AGENTS:
            assert agent in ROUTER_SYSTEM_PROMPT

    def test_prompt_enforces_scoping(self):
        assert "OUT-OF-SCOPE" in ROUTER_SYSTEM_PROMPT.upper()
        assert "[]" in ROUTER_SYSTEM_PROMPT