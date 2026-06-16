"""MCP tools for crm.lead — leads and opportunities CRUD + pipeline actions."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import OdooClient

LEAD_FIELDS = [
    "id", "name", "type", "partner_id", "contact_name", "email_from", "phone", "mobile",
    "team_id", "user_id", "stage_id", "kanban_state", "priority", "probability",
    "expected_revenue", "prorated_revenue", "date_deadline", "date_closed",
    "tag_ids", "description", "active", "lost_reason_id", "campaign_id",
    "medium_id", "source_id", "referred", "street", "city", "state_id", "country_id",
    "create_date", "write_date", "activity_ids", "message_ids",
]

LEAD_FIELDS_BRIEF = [
    "id", "name", "type", "partner_id", "contact_name", "email_from", "phone",
    "team_id", "user_id", "stage_id", "priority", "probability", "expected_revenue",
    "date_deadline", "kanban_state", "active", "tag_ids", "create_date",
]


def register_lead_tools(mcp: FastMCP, get_client):
    """Register all crm.lead tools into the FastMCP instance."""

    @mcp.tool()
    async def list_leads(
        type: str = "all",
        stage_id: int | None = None,
        team_id: int | None = None,
        user_id: int | None = None,
        active: bool = True,
        limit: int = 50,
        offset: int = 0,
        order: str = "date_deadline asc, priority desc",
    ) -> list[dict]:
        """List CRM leads and/or opportunities with optional filters.

        Args:
            type: Filter by record type — 'lead', 'opportunity', or 'all'.
            stage_id: Filter by pipeline stage ID.
            team_id: Filter by sales team ID.
            user_id: Filter by assigned salesperson ID.
            active: True for active records, False for archived.
            limit: Maximum number of records to return (default 50, max 200).
            offset: Pagination offset.
            order: Sort order (Odoo ORM syntax).
        """
        client: OdooClient = await get_client()
        domain: list[Any] = [("active", "=", active)]
        if type != "all":
            domain.append(("type", "=", type))
        if stage_id:
            domain.append(("stage_id", "=", stage_id))
        if team_id:
            domain.append(("team_id", "=", team_id))
        if user_id:
            domain.append(("user_id", "=", user_id))

        return await client.search_read("crm.lead", domain, LEAD_FIELDS_BRIEF, min(limit, 200), offset, order)

    @mcp.tool()
    async def search_leads(
        query: str,
        search_in: str = "name,email,phone,contact_name",
        type: str = "all",
        limit: int = 30,
    ) -> list[dict]:
        """Full-text search across leads and opportunities.

        Args:
            query: Search string (name, email, phone, or contact name).
            search_in: Comma-separated list of fields to search. Options: name, email_from, phone, contact_name, description.
            type: Filter by 'lead', 'opportunity', or 'all'.
            limit: Maximum results.
        """
        client: OdooClient = await get_client()
        fields = [f.strip() for f in search_in.split(",")]
        domain: list[Any] = ["|"] * (len(fields) - 1)
        for field in fields:
            domain.append((field, "ilike", query))

        if type != "all":
            domain = ["&", ("type", "=", type)] + domain

        return await client.search_read("crm.lead", domain, LEAD_FIELDS_BRIEF, limit)

    @mcp.tool()
    async def get_lead(lead_id: int) -> dict:
        """Get full details of a single lead or opportunity by ID.

        Args:
            lead_id: The crm.lead record ID.
        """
        client: OdooClient = await get_client()
        records = await client.read("crm.lead", [lead_id], LEAD_FIELDS)
        if not records:
            raise ValueError(f"Lead {lead_id} not found")
        return records[0]

    @mcp.tool()
    async def create_lead(
        name: str,
        type: str = "lead",
        contact_name: str | None = None,
        partner_id: int | None = None,
        email_from: str | None = None,
        phone: str | None = None,
        mobile: str | None = None,
        team_id: int | None = None,
        user_id: int | None = None,
        stage_id: int | None = None,
        priority: str = "0",
        expected_revenue: float | None = None,
        probability: float | None = None,
        date_deadline: str | None = None,
        description: str | None = None,
        tag_ids: list[int] | None = None,
        street: str | None = None,
        city: str | None = None,
        country_id: int | None = None,
        campaign_id: int | None = None,
        source_id: int | None = None,
        medium_id: int | None = None,
    ) -> dict:
        """Create a new CRM lead or opportunity.

        Args:
            name: Lead/opportunity title (required).
            type: 'lead' for an unqualified lead or 'opportunity' for a qualified opportunity.
            contact_name: Contact person name (if no linked partner).
            partner_id: ID of an existing res.partner to link.
            email_from: Contact email address.
            phone: Contact phone number.
            mobile: Contact mobile number.
            team_id: Sales team ID.
            user_id: Salesperson user ID.
            stage_id: Pipeline stage ID.
            priority: '0' = Normal, '1' = Low, '2' = High, '3' = Very High.
            expected_revenue: Expected revenue amount.
            probability: Win probability percentage (0-100).
            date_deadline: Expected closing date (YYYY-MM-DD).
            description: Internal notes / description.
            tag_ids: List of crm.tag IDs to apply.
            street: Street address.
            city: City.
            country_id: Country ID (res.country).
            campaign_id: Marketing campaign ID.
            source_id: Traffic source ID.
            medium_id: Marketing medium ID.
        """
        client: OdooClient = await get_client()
        values: dict[str, Any] = {"name": name, "type": type, "priority": priority}

        optional_fields = {
            "contact_name": contact_name, "partner_id": partner_id,
            "email_from": email_from, "phone": phone, "mobile": mobile,
            "team_id": team_id, "user_id": user_id, "stage_id": stage_id,
            "expected_revenue": expected_revenue, "probability": probability,
            "date_deadline": date_deadline, "description": description,
            "street": street, "city": city, "country_id": country_id,
            "campaign_id": campaign_id, "source_id": source_id, "medium_id": medium_id,
        }
        for key, val in optional_fields.items():
            if val is not None:
                values[key] = val

        if tag_ids:
            values["tag_ids"] = [(6, 0, tag_ids)]

        lead_id = await client.create("crm.lead", values)
        records = await client.read("crm.lead", [lead_id], LEAD_FIELDS)
        return records[0]

    @mcp.tool()
    async def update_lead(
        lead_id: int,
        name: str | None = None,
        contact_name: str | None = None,
        partner_id: int | None = None,
        email_from: str | None = None,
        phone: str | None = None,
        mobile: str | None = None,
        team_id: int | None = None,
        user_id: int | None = None,
        stage_id: int | None = None,
        priority: str | None = None,
        expected_revenue: float | None = None,
        probability: float | None = None,
        date_deadline: str | None = None,
        description: str | None = None,
        tag_ids: list[int] | None = None,
        kanban_state: str | None = None,
        street: str | None = None,
        city: str | None = None,
        country_id: int | None = None,
    ) -> dict:
        """Update fields on an existing lead or opportunity.

        Args:
            lead_id: ID of the crm.lead record to update.
            name: New title.
            contact_name: Contact person name.
            partner_id: Link to an existing res.partner.
            email_from: Email address.
            phone: Phone number.
            mobile: Mobile number.
            team_id: Sales team ID.
            user_id: Salesperson user ID.
            stage_id: Move to a different pipeline stage.
            priority: '0'=Normal, '1'=Low, '2'=High, '3'=Very High.
            expected_revenue: Expected revenue.
            probability: Win probability (0-100).
            date_deadline: Expected closing date (YYYY-MM-DD).
            description: Internal notes.
            tag_ids: Replace tag list with these crm.tag IDs.
            kanban_state: 'normal', 'done' (ready for next stage), or 'blocked'.
            street: Street address.
            city: City.
            country_id: Country ID.
        """
        client: OdooClient = await get_client()
        values: dict[str, Any] = {}

        optional_fields = {
            "name": name, "contact_name": contact_name, "partner_id": partner_id,
            "email_from": email_from, "phone": phone, "mobile": mobile,
            "team_id": team_id, "user_id": user_id, "stage_id": stage_id,
            "priority": priority, "expected_revenue": expected_revenue,
            "probability": probability, "date_deadline": date_deadline,
            "description": description, "kanban_state": kanban_state,
            "street": street, "city": city, "country_id": country_id,
        }
        for key, val in optional_fields.items():
            if val is not None:
                values[key] = val

        if tag_ids is not None:
            values["tag_ids"] = [(6, 0, tag_ids)]

        if not values:
            raise ValueError("No fields provided to update")

        await client.write("crm.lead", [lead_id], values)
        records = await client.read("crm.lead", [lead_id], LEAD_FIELDS)
        return records[0]

    @mcp.tool()
    async def delete_lead(lead_id: int) -> dict:
        """Permanently delete a lead or opportunity.

        Args:
            lead_id: ID of the crm.lead record to delete.
        """
        client: OdooClient = await get_client()
        await client.unlink("crm.lead", [lead_id])
        return {"success": True, "deleted_id": lead_id}

    @mcp.tool()
    async def archive_lead(lead_id: int) -> dict:
        """Archive (soft-delete) a lead or opportunity instead of permanently deleting it.

        Args:
            lead_id: ID of the crm.lead record to archive.
        """
        client: OdooClient = await get_client()
        await client.write("crm.lead", [lead_id], {"active": False})
        return {"success": True, "archived_id": lead_id}

    @mcp.tool()
    async def unarchive_lead(lead_id: int) -> dict:
        """Restore an archived lead or opportunity.

        Args:
            lead_id: ID of the archived crm.lead record to restore.
        """
        client: OdooClient = await get_client()
        await client.write("crm.lead", [lead_id], {"active": True})
        return {"success": True, "unarchived_id": lead_id}

    @mcp.tool()
    async def mark_lead_won(lead_id: int) -> dict:
        """Mark a lead/opportunity as Won and close it.

        Args:
            lead_id: ID of the crm.lead record to mark as won.
        """
        client: OdooClient = await get_client()
        await client.call_method("crm.lead", "action_set_won", [lead_id])
        records = await client.read("crm.lead", [lead_id], LEAD_FIELDS_BRIEF)
        return records[0] if records else {"id": lead_id, "status": "won"}

    @mcp.tool()
    async def mark_lead_lost(lead_id: int, lost_reason_id: int | None = None) -> dict:
        """Mark a lead/opportunity as Lost and close it.

        Args:
            lead_id: ID of the crm.lead record to mark as lost.
            lost_reason_id: Optional crm.lost.reason ID explaining why it was lost.
        """
        client: OdooClient = await get_client()
        kwargs: dict[str, Any] = {}
        if lost_reason_id:
            kwargs["lost_reason_id"] = lost_reason_id
        await client.call_method("crm.lead", "action_set_lost", [lead_id], **kwargs)
        records = await client.read("crm.lead", [lead_id], LEAD_FIELDS_BRIEF)
        return records[0] if records else {"id": lead_id, "status": "lost"}

    @mcp.tool()
    async def convert_lead_to_opportunity(
        lead_id: int,
        partner_id: int | None = None,
        team_id: int | None = None,
        user_id: int | None = None,
        merge_lead_ids: list[int] | None = None,
    ) -> dict:
        """Convert a lead into a qualified opportunity (and optionally merge duplicates).

        Args:
            lead_id: ID of the crm.lead (type='lead') to convert.
            partner_id: Link or create a res.partner. If None, Odoo auto-matches by email.
            team_id: Assign to this sales team.
            user_id: Assign to this salesperson.
            merge_lead_ids: List of duplicate lead IDs to merge into this one during conversion.
        """
        client: OdooClient = await get_client()
        values: dict[str, Any] = {"lead_id": lead_id}
        if partner_id:
            values["partner_id"] = partner_id
        if team_id:
            values["team_id"] = team_id
        if user_id:
            values["user_ids"] = [user_id]
        if merge_lead_ids:
            values["opportunity_ids"] = merge_lead_ids

        wizard_id = await client.execute_kw(
            "crm.convert.lead",
            "create",
            [{"lead_id": lead_id}],
        )
        result = await client.execute_kw(
            "crm.convert.lead",
            "action_convert",
            [[wizard_id]],
        )
        records = await client.read("crm.lead", [lead_id], LEAD_FIELDS_BRIEF)
        return records[0] if records else {"id": lead_id, "type": "opportunity", "result": result}

    @mcp.tool()
    async def move_lead_to_stage(lead_id: int, stage_id: int) -> dict:
        """Move a lead or opportunity to a specific pipeline stage.

        Args:
            lead_id: ID of the crm.lead record.
            stage_id: Target crm.stage ID.
        """
        client: OdooClient = await get_client()
        await client.write("crm.lead", [lead_id], {"stage_id": stage_id})
        records = await client.read("crm.lead", [lead_id], LEAD_FIELDS_BRIEF)
        return records[0]

    @mcp.tool()
    async def assign_lead(lead_id: int, user_id: int, team_id: int | None = None) -> dict:
        """Assign a lead or opportunity to a salesperson (and optionally a sales team).

        Args:
            lead_id: ID of the crm.lead record.
            user_id: ID of the res.users to assign as salesperson.
            team_id: Optional crm.team ID to reassign the team as well.
        """
        client: OdooClient = await get_client()
        values: dict[str, Any] = {"user_id": user_id}
        if team_id:
            values["team_id"] = team_id
        await client.write("crm.lead", [lead_id], values)
        records = await client.read("crm.lead", [lead_id], LEAD_FIELDS_BRIEF)
        return records[0]

    @mcp.tool()
    async def get_lost_reasons() -> list[dict]:
        """Get all available lost reasons for marking opportunities as lost."""
        client: OdooClient = await get_client()
        return await client.search_read(
            "crm.lost.reason",
            [],
            ["id", "name", "active"],
            limit=100,
        )

    @mcp.tool()
    async def bulk_update_leads(
        lead_ids: list[int],
        stage_id: int | None = None,
        user_id: int | None = None,
        team_id: int | None = None,
        priority: str | None = None,
        tag_ids: list[int] | None = None,
    ) -> dict:
        """Update multiple leads/opportunities at once (bulk operation).

        Args:
            lead_ids: List of crm.lead IDs to update.
            stage_id: Move all to this stage.
            user_id: Reassign all to this salesperson.
            team_id: Reassign all to this sales team.
            priority: Set priority for all ('0'=Normal, '1'=Low, '2'=High, '3'=Very High).
            tag_ids: Replace tags on all records with these crm.tag IDs.
        """
        client: OdooClient = await get_client()
        values: dict[str, Any] = {}
        if stage_id is not None:
            values["stage_id"] = stage_id
        if user_id is not None:
            values["user_id"] = user_id
        if team_id is not None:
            values["team_id"] = team_id
        if priority is not None:
            values["priority"] = priority
        if tag_ids is not None:
            values["tag_ids"] = [(6, 0, tag_ids)]
        if not values:
            raise ValueError("No fields to update")
        await client.write("crm.lead", lead_ids, values)
        return {"success": True, "updated_count": len(lead_ids), "updated_ids": lead_ids}
