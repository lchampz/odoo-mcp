"""MCP tools for res.users — salesperson/user lookup."""

from mcp.server.fastmcp import FastMCP

from ..client import OdooClient


def register_user_tools(mcp: FastMCP, get_client):
    """Register user-lookup tools."""

    @mcp.tool()
    async def list_salespersons(team_id: int | None = None) -> list[dict]:
        """List all users who are salespersons in the CRM, optionally filtered by team.

        Args:
            team_id: Filter to members of a specific sales team.
        """
        client: OdooClient = await get_client()
        if team_id:
            team = await client.read("crm.team", [team_id], ["member_ids"])
            if not team:
                raise ValueError(f"Team {team_id} not found")
            member_ids = team[0].get("member_ids", [])
            if not member_ids:
                return []
            domain = [("id", "in", member_ids)]
        else:
            domain = [("share", "=", False), ("active", "=", True)]

        return await client.search_read(
            "res.users",
            domain,
            ["id", "name", "email", "login", "groups_id"],
            limit=200,
            order="name asc",
        )

    @mcp.tool()
    async def get_current_user() -> dict:
        """Get information about the currently authenticated Odoo user."""
        client: OdooClient = await get_client()
        records = await client.read(
            "res.users",
            [client.uid],
            ["id", "name", "email", "login", "lang", "tz", "company_id"],
        )
        return records[0] if records else {"uid": client.uid}

    @mcp.tool()
    async def search_users(query: str) -> list[dict]:
        """Search for Odoo users by name or email.

        Args:
            query: Search string matched against name or email.
        """
        client: OdooClient = await get_client()
        return await client.search_read(
            "res.users",
            ["|", ("name", "ilike", query), ("email", "ilike", query), ("active", "=", True)],
            ["id", "name", "email", "login"],
            limit=30,
        )
