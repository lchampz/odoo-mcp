"""MCP tools for crm.stage — pipeline stage management."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import OdooClient

STAGE_FIELDS = ["id", "name", "sequence", "probability", "requirements", "team_id", "fold", "is_won"]


def register_stage_tools(mcp: FastMCP, get_client):
    """Register all crm.stage tools."""

    @mcp.tool()
    async def list_stages(team_id: int | None = None) -> list[dict]:
        """List all pipeline stages, optionally filtered by sales team.

        Args:
            team_id: Filter stages belonging to a specific sales team. None returns all stages.
        """
        client: OdooClient = await get_client()
        domain: list[Any] = []
        if team_id:
            domain = ["|", ("team_id", "=", team_id), ("team_id", "=", False)]
        return await client.search_read("crm.stage", domain, STAGE_FIELDS, limit=100, order="sequence asc")

    @mcp.tool()
    async def get_stage(stage_id: int) -> dict:
        """Get details of a single pipeline stage.

        Args:
            stage_id: The crm.stage record ID.
        """
        client: OdooClient = await get_client()
        records = await client.read("crm.stage", [stage_id], STAGE_FIELDS)
        if not records:
            raise ValueError(f"Stage {stage_id} not found")
        return records[0]

    @mcp.tool()
    async def create_stage(
        name: str,
        sequence: int = 10,
        probability: float = 20.0,
        requirements: str | None = None,
        team_id: int | None = None,
        fold: bool = False,
        is_won: bool = False,
    ) -> dict:
        """Create a new pipeline stage.

        Args:
            name: Stage name (e.g. 'Qualified', 'Proposal', 'Negotiation').
            sequence: Order in the pipeline (lower = earlier). Default 10.
            probability: Default win probability % for leads in this stage (0-100).
            requirements: Optional description of what qualifies a lead for this stage.
            team_id: Restrict this stage to a specific sales team. None = visible to all.
            fold: Whether to fold (collapse) this stage in the Kanban view by default.
            is_won: Mark this stage as the Won stage (sets probability to 100%).
        """
        client: OdooClient = await get_client()
        values: dict[str, Any] = {
            "name": name,
            "sequence": sequence,
            "probability": probability,
            "fold": fold,
            "is_won": is_won,
        }
        if requirements:
            values["requirements"] = requirements
        if team_id:
            values["team_id"] = team_id

        stage_id = await client.create("crm.stage", values)
        records = await client.read("crm.stage", [stage_id], STAGE_FIELDS)
        return records[0]

    @mcp.tool()
    async def update_stage(
        stage_id: int,
        name: str | None = None,
        sequence: int | None = None,
        probability: float | None = None,
        requirements: str | None = None,
        team_id: int | None = None,
        fold: bool | None = None,
    ) -> dict:
        """Update an existing pipeline stage.

        Args:
            stage_id: The crm.stage record ID to update.
            name: New stage name.
            sequence: New order position.
            probability: Default win probability %.
            requirements: Entry criteria description.
            team_id: Change or remove the team restriction (use 0 or False to make global).
            fold: Whether to collapse in Kanban view.
        """
        client: OdooClient = await get_client()
        values: dict[str, Any] = {}
        for key, val in [
            ("name", name), ("sequence", sequence), ("probability", probability),
            ("requirements", requirements), ("team_id", team_id), ("fold", fold),
        ]:
            if val is not None:
                values[key] = val
        if not values:
            raise ValueError("No fields to update")
        await client.write("crm.stage", [stage_id], values)
        records = await client.read("crm.stage", [stage_id], STAGE_FIELDS)
        return records[0]

    @mcp.tool()
    async def delete_stage(stage_id: int) -> dict:
        """Delete a pipeline stage. Fails if leads are still in this stage.

        Args:
            stage_id: The crm.stage record ID to delete.
        """
        client: OdooClient = await get_client()
        count = await client.search_count("crm.lead", [("stage_id", "=", stage_id), ("active", "=", True)])
        if count > 0:
            raise ValueError(
                f"Cannot delete stage {stage_id} — it still contains {count} active lead(s). "
                "Move them to another stage first."
            )
        await client.unlink("crm.stage", [stage_id])
        return {"success": True, "deleted_id": stage_id}

    @mcp.tool()
    async def reorder_stages(stage_sequences: list[dict]) -> dict:
        """Reorder pipeline stages by setting their sequence numbers.

        Args:
            stage_sequences: List of dicts with 'id' and 'sequence' keys.
                             Example: [{"id": 1, "sequence": 10}, {"id": 2, "sequence": 20}]
        """
        client: OdooClient = await get_client()
        for item in stage_sequences:
            await client.write("crm.stage", [item["id"]], {"sequence": item["sequence"]})
        return {"success": True, "reordered_count": len(stage_sequences)}
