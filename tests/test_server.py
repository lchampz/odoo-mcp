"""Tests for server tool registration and config validation."""

import os
import pytest

from odoo_crm_mcp.server import mcp


def test_all_tools_registered():
    """Verify the expected tools are registered in the MCP server."""
    tool_names = {t.name for t in mcp._tool_manager.list_tools()}

    expected = {
        # leads
        "list_leads", "search_leads", "get_lead", "create_lead", "update_lead",
        "delete_lead", "archive_lead", "unarchive_lead", "mark_lead_won", "mark_lead_lost",
        "convert_lead_to_opportunity", "move_lead_to_stage", "assign_lead",
        "get_lost_reasons", "bulk_update_leads",
        # stages
        "list_stages", "get_stage", "create_stage", "update_stage", "delete_stage", "reorder_stages",
        # teams
        "list_teams", "get_team", "create_team", "update_team",
        "add_team_member", "remove_team_member", "get_team_pipeline",
        # activities
        "list_activity_types", "schedule_activity", "list_lead_activities",
        "list_my_activities", "mark_activity_done", "cancel_activity",
        "reschedule_activity", "log_note_on_lead", "send_message_on_lead", "get_lead_messages",
        # contacts
        "search_contacts", "get_contact", "create_contact", "update_contact",
        "get_contact_opportunities", "list_countries", "list_states",
        # tags
        "list_tags", "create_tag", "update_tag", "delete_tag",
        # analytics
        "get_pipeline_summary", "get_won_lost_analysis", "get_salesperson_performance",
        "get_leads_by_source", "get_overdue_opportunities", "get_pipeline_forecast",
        "get_conversion_funnel", "get_leads_created_this_week",
        # users
        "list_salespersons", "get_current_user", "search_users",
        # utility
        "ping",
    }

    missing = expected - tool_names
    assert not missing, f"Missing tools: {missing}"


def test_missing_env_raises(monkeypatch):
    """Config should raise EnvironmentError if env vars are missing."""
    from odoo_crm_mcp.server import _get_config

    for var in ["ODOO_URL", "ODOO_DATABASE", "ODOO_USERNAME", "ODOO_PASSWORD"]:
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(EnvironmentError, match="Missing required environment variables"):
        _get_config()
