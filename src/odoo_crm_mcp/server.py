"""Odoo CRM MCP Server — entry point and tool registration."""

import argparse
import logging
import os
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .client import OdooClient
from .tools.activities import register_activity_tools
from .tools.analytics import register_analytics_tools
from .tools.contacts import register_contact_tools
from .tools.leads import register_lead_tools
from .tools.stages import register_stage_tools
from .tools.tags import register_tag_tools
from .tools.teams import register_team_tools
from .tools.users import register_user_tools

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_config() -> dict[str, str]:
    url = os.environ.get("ODOO_URL", "")
    database = os.environ.get("ODOO_DATABASE", "")
    username = os.environ.get("ODOO_USERNAME", "")
    password = os.environ.get("ODOO_PASSWORD", "")

    missing = [k for k, v in {"ODOO_URL": url, "ODOO_DATABASE": database,
                               "ODOO_USERNAME": username, "ODOO_PASSWORD": password}.items() if not v]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Set them in a .env file or as environment variables. See README.md for details."
        )
    return {"url": url, "database": database, "username": username, "password": password}


_client_instance: OdooClient | None = None


async def get_client() -> OdooClient:
    """Return a cached, authenticated OdooClient. Re-authenticates if uid is missing."""
    global _client_instance
    if _client_instance is None:
        cfg = _get_config()
        _client_instance = OdooClient(**cfg)
        await _client_instance.authenticate()
    return _client_instance


mcp = FastMCP(
    name="odoo-crm",
    instructions="""You are connected to an Odoo CRM instance.

Available capabilities:
- **Leads & Opportunities**: Create, read, update, delete, search, bulk-update, convert, win/lose
- **Pipeline Stages**: List, create, update, delete, reorder stages
- **Sales Teams**: List, create, update teams, add/remove members, view team pipeline
- **Activities**: Schedule, list, complete, cancel activities (calls, emails, meetings)
- **Contacts**: Search, create, update contacts/companies linked to CRM
- **Tags**: Manage CRM tags for labelling leads
- **Analytics**: Pipeline summary, won/lost analysis, salesperson performance, forecasting, funnel
- **Users**: List salespersons, get current user info

Tips:
- Use `list_stages` first to get stage IDs before creating leads.
- Use `list_teams` to get team IDs for filtering.
- Use `search_leads` for quick lookup by name/email/phone.
- Use `get_pipeline_summary` for an overview of the current pipeline.
""",
)


register_lead_tools(mcp, get_client)
register_stage_tools(mcp, get_client)
register_team_tools(mcp, get_client)
register_activity_tools(mcp, get_client)
register_contact_tools(mcp, get_client)
register_tag_tools(mcp, get_client)
register_analytics_tools(mcp, get_client)
register_user_tools(mcp, get_client)


@mcp.tool()
async def ping() -> dict:
    """Test the connection to Odoo and return server info.

    Returns basic Odoo server information to verify the connection is working.
    """
    client = await get_client()
    version = await client._jsonrpc("/web/webclient/version_info")
    return {
        "status": "connected",
        "odoo_url": os.environ.get("ODOO_URL"),
        "database": os.environ.get("ODOO_DATABASE"),
        "authenticated_uid": client.uid,
        "server_version": version.get("server_version") if version else "unknown",
    }


def main():
    parser = argparse.ArgumentParser(description="Odoo CRM MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol. Use 'stdio' for Claude Desktop/Code, 'sse' or 'streamable-http' for n8n/web.",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (HTTP modes only)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (HTTP modes only)")
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    elif args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
