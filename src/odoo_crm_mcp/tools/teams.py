"""MCP tools for crm.team — sales team management."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import OdooClient

TEAM_FIELDS = [
    "id", "name", "active", "user_id", "member_ids", "color",
    "stage_ids", "alias_id", "company_id", "currency_id",
]

TEAM_FIELDS_BRIEF = ["id", "name", "active", "user_id", "member_ids", "color"]


def register_team_tools(mcp: FastMCP, get_client):
    """Register all crm.team tools."""

    @mcp.tool()
    async def list_teams(active: bool = True) -> list[dict]:
        """List all CRM sales teams.

        Args:
            active: True to list active teams, False for archived teams.
        """
        client: OdooClient = await get_client()
        return await client.search_read(
            "crm.team",
            [("active", "=", active)],
            TEAM_FIELDS_BRIEF,
            limit=100,
        )

    @mcp.tool()
    async def get_team(team_id: int) -> dict:
        """Get details of a specific sales team.

        Args:
            team_id: The crm.team record ID.
        """
        client: OdooClient = await get_client()
        records = await client.read("crm.team", [team_id], TEAM_FIELDS)
        if not records:
            raise ValueError(f"Sales team {team_id} not found")
        return records[0]

    @mcp.tool()
    async def create_team(
        name: str,
        user_id: int | None = None,
        member_ids: list[int] | None = None,
        alias_name: str | None = None,
    ) -> dict:
        """Create a new sales team.

        Args:
            name: Team name.
            user_id: Team leader (res.users ID).
            member_ids: List of salesperson IDs (res.users) to add as team members.
            alias_name: Email alias name for the team (e.g. 'sales' → leads@yourdomain.com).
        """
        client: OdooClient = await get_client()
        values: dict[str, Any] = {"name": name}
        if user_id:
            values["user_id"] = user_id
        if member_ids:
            values["member_ids"] = [(6, 0, member_ids)]
        if alias_name:
            values["alias_name"] = alias_name

        team_id = await client.create("crm.team", values)
        records = await client.read("crm.team", [team_id], TEAM_FIELDS)
        return records[0]

    @mcp.tool()
    async def update_team(
        team_id: int,
        name: str | None = None,
        user_id: int | None = None,
        member_ids: list[int] | None = None,
    ) -> dict:
        """Update an existing sales team.

        Args:
            team_id: The crm.team record ID to update.
            name: New team name.
            user_id: New team leader.
            member_ids: Replace the member list with these user IDs.
        """
        client: OdooClient = await get_client()
        values: dict[str, Any] = {}
        if name is not None:
            values["name"] = name
        if user_id is not None:
            values["user_id"] = user_id
        if member_ids is not None:
            values["member_ids"] = [(6, 0, member_ids)]
        if not values:
            raise ValueError("No fields to update")
        await client.write("crm.team", [team_id], values)
        records = await client.read("crm.team", [team_id], TEAM_FIELDS)
        return records[0]

    @mcp.tool()
    async def add_team_member(team_id: int, user_id: int) -> dict:
        """Add a salesperson to a sales team.

        Args:
            team_id: The crm.team record ID.
            user_id: The res.users ID of the salesperson to add.
        """
        client: OdooClient = await get_client()
        await client.execute_kw(
            "crm.team", "write", [[team_id], {"member_ids": [(4, user_id)]}]
        )
        records = await client.read("crm.team", [team_id], TEAM_FIELDS)
        return records[0]

    @mcp.tool()
    async def remove_team_member(team_id: int, user_id: int) -> dict:
        """Remove a salesperson from a sales team.

        Args:
            team_id: The crm.team record ID.
            user_id: The res.users ID of the salesperson to remove.
        """
        client: OdooClient = await get_client()
        await client.execute_kw(
            "crm.team", "write", [[team_id], {"member_ids": [(3, user_id)]}]
        )
        records = await client.read("crm.team", [team_id], TEAM_FIELDS)
        return records[0]

    @mcp.tool()
    async def get_team_pipeline(team_id: int, limit: int = 50) -> dict:
        """Get all active opportunities grouped by stage for a specific sales team.

        Args:
            team_id: The crm.team record ID.
            limit: Maximum leads to return per stage (default 50).
        """
        client: OdooClient = await get_client()
        stages = await client.search_read(
            "crm.stage",
            ["|", ("team_id", "=", team_id), ("team_id", "=", False)],
            ["id", "name", "sequence"],
            limit=50,
            order="sequence asc",
        )
        pipeline = []
        for stage in stages:
            leads = await client.search_read(
                "crm.lead",
                [("team_id", "=", team_id), ("stage_id", "=", stage["id"]), ("active", "=", True)],
                ["id", "name", "partner_id", "user_id", "expected_revenue", "probability", "date_deadline"],
                limit=limit,
            )
            total_revenue = sum(l.get("expected_revenue") or 0 for l in leads)
            pipeline.append({
                "stage": stage,
                "leads_count": len(leads),
                "total_expected_revenue": total_revenue,
                "leads": leads,
            })
        return {"team_id": team_id, "stages": pipeline}
