"""MCP tools for crm.tag — lead and opportunity tag management."""

from mcp.server.fastmcp import FastMCP

from ..client import OdooClient


def register_tag_tools(mcp: FastMCP, get_client):
    """Register all crm.tag tools."""

    @mcp.tool()
    async def list_tags() -> list[dict]:
        """List all available CRM tags."""
        client: OdooClient = await get_client()
        return await client.search_read(
            "crm.tag",
            [],
            ["id", "name", "color"],
            limit=200,
            order="name asc",
        )

    @mcp.tool()
    async def create_tag(name: str, color: int = 0) -> dict:
        """Create a new CRM tag.

        Args:
            name: Tag label (e.g. 'Hot Lead', 'Enterprise', 'Follow-up').
            color: Color index 0-11 for the tag chip in Odoo UI.
        """
        client: OdooClient = await get_client()
        tag_id = await client.create("crm.tag", {"name": name, "color": color})
        records = await client.read("crm.tag", [tag_id], ["id", "name", "color"])
        return records[0]

    @mcp.tool()
    async def update_tag(tag_id: int, name: str | None = None, color: int | None = None) -> dict:
        """Update an existing CRM tag.

        Args:
            tag_id: The crm.tag record ID.
            name: New tag label.
            color: New color index (0-11).
        """
        client: OdooClient = await get_client()
        values = {}
        if name is not None:
            values["name"] = name
        if color is not None:
            values["color"] = color
        if not values:
            raise ValueError("No fields to update")
        await client.write("crm.tag", [tag_id], values)
        records = await client.read("crm.tag", [tag_id], ["id", "name", "color"])
        return records[0]

    @mcp.tool()
    async def delete_tag(tag_id: int) -> dict:
        """Delete a CRM tag. The tag will be removed from all leads.

        Args:
            tag_id: The crm.tag record ID to delete.
        """
        client: OdooClient = await get_client()
        await client.unlink("crm.tag", [tag_id])
        return {"success": True, "deleted_id": tag_id}
