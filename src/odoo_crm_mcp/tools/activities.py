"""MCP tools for mail.activity — CRM activity scheduling and tracking."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import OdooClient

ACTIVITY_FIELDS = [
    "id", "res_id", "res_name", "activity_type_id", "summary", "note",
    "date_deadline", "user_id", "state", "icon",
]


def register_activity_tools(mcp: FastMCP, get_client):
    """Register all activity-related tools."""

    @mcp.tool()
    async def list_activity_types() -> list[dict]:
        """List all available activity types (call, email, meeting, etc.)."""
        client: OdooClient = await get_client()
        return await client.search_read(
            "mail.activity.type",
            [("res_model", "in", ["crm.lead", False])],
            ["id", "name", "icon", "delay_count", "delay_unit", "res_model"],
            limit=50,
        )

    @mcp.tool()
    async def schedule_activity(
        lead_id: int,
        activity_type_id: int,
        date_deadline: str,
        summary: str | None = None,
        note: str | None = None,
        user_id: int | None = None,
    ) -> dict:
        """Schedule an activity (call, email, meeting, etc.) on a lead or opportunity.

        Args:
            lead_id: ID of the crm.lead to attach the activity to.
            activity_type_id: ID of the mail.activity.type (use list_activity_types to find IDs).
            date_deadline: Due date in YYYY-MM-DD format.
            summary: Short summary / title of the activity.
            note: Detailed notes or instructions for the activity.
            user_id: Assign to this user. Defaults to the authenticated user.
        """
        client: OdooClient = await get_client()
        values: dict[str, Any] = {
            "res_model_id": await _get_crm_lead_model_id(client),
            "res_id": lead_id,
            "activity_type_id": activity_type_id,
            "date_deadline": date_deadline,
        }
        if summary:
            values["summary"] = summary
        if note:
            values["note"] = note
        if user_id:
            values["user_id"] = user_id

        activity_id = await client.create("mail.activity", values)
        records = await client.read("mail.activity", [activity_id], ACTIVITY_FIELDS)
        return records[0]

    @mcp.tool()
    async def list_lead_activities(lead_id: int) -> list[dict]:
        """List all scheduled activities for a specific lead or opportunity.

        Args:
            lead_id: ID of the crm.lead record.
        """
        client: OdooClient = await get_client()
        return await client.search_read(
            "mail.activity",
            [("res_id", "=", lead_id), ("res_model", "=", "crm.lead")],
            ACTIVITY_FIELDS,
            limit=50,
        )

    @mcp.tool()
    async def list_my_activities(
        overdue_only: bool = False,
        today_only: bool = False,
        limit: int = 50,
    ) -> list[dict]:
        """List activities assigned to the current user across all leads.

        Args:
            overdue_only: If True, return only overdue activities.
            today_only: If True, return only activities due today.
            limit: Maximum number of activities to return.
        """
        client: OdooClient = await get_client()
        domain: list[Any] = [
            ("res_model", "=", "crm.lead"),
            ("user_id", "=", client.uid),
        ]
        if overdue_only:
            from datetime import date
            domain.append(("date_deadline", "<", date.today().isoformat()))
        elif today_only:
            from datetime import date
            today = date.today().isoformat()
            domain += [("date_deadline", ">=", today), ("date_deadline", "<=", today)]

        return await client.search_read(
            "mail.activity",
            domain,
            ACTIVITY_FIELDS + ["res_name"],
            limit=limit,
            order="date_deadline asc",
        )

    @mcp.tool()
    async def mark_activity_done(
        activity_id: int,
        feedback: str | None = None,
    ) -> dict:
        """Mark an activity as done (completed).

        Args:
            activity_id: ID of the mail.activity to mark as done.
            feedback: Optional completion note to log on the lead's chatter.
        """
        client: OdooClient = await get_client()
        kwargs: dict[str, Any] = {}
        if feedback:
            kwargs["feedback"] = feedback
        await client.call_method("mail.activity", "action_done", [activity_id], **kwargs)
        return {"success": True, "done_activity_id": activity_id}

    @mcp.tool()
    async def cancel_activity(activity_id: int) -> dict:
        """Cancel and delete a scheduled activity.

        Args:
            activity_id: ID of the mail.activity to cancel.
        """
        client: OdooClient = await get_client()
        await client.unlink("mail.activity", [activity_id])
        return {"success": True, "cancelled_activity_id": activity_id}

    @mcp.tool()
    async def reschedule_activity(activity_id: int, new_date_deadline: str) -> dict:
        """Reschedule an activity to a new due date.

        Args:
            activity_id: ID of the mail.activity to reschedule.
            new_date_deadline: New due date in YYYY-MM-DD format.
        """
        client: OdooClient = await get_client()
        await client.write("mail.activity", [activity_id], {"date_deadline": new_date_deadline})
        records = await client.read("mail.activity", [activity_id], ACTIVITY_FIELDS)
        return records[0]

    @mcp.tool()
    async def log_note_on_lead(lead_id: int, body: str) -> dict:
        """Log an internal note on a lead's chatter (not visible to customer).

        Args:
            lead_id: ID of the crm.lead record.
            body: The note content (can include HTML).
        """
        client: OdooClient = await get_client()
        result = await client.execute_kw(
            "crm.lead",
            "message_post",
            [[lead_id]],
            {"body": body, "message_type": "comment", "subtype_xmlid": "mail.mt_note"},
        )
        return {"success": True, "message_id": result}

    @mcp.tool()
    async def send_message_on_lead(lead_id: int, body: str, partner_ids: list[int] | None = None) -> dict:
        """Send a message on a lead's chatter (can notify followers).

        Args:
            lead_id: ID of the crm.lead record.
            body: The message content (can include HTML).
            partner_ids: List of res.partner IDs to notify (in addition to followers).
        """
        client: OdooClient = await get_client()
        kwargs: dict[str, Any] = {"body": body, "message_type": "comment"}
        if partner_ids:
            kwargs["partner_ids"] = partner_ids
        result = await client.execute_kw(
            "crm.lead",
            "message_post",
            [[lead_id]],
            kwargs,
        )
        return {"success": True, "message_id": result}

    @mcp.tool()
    async def get_lead_messages(lead_id: int, limit: int = 20) -> list[dict]:
        """Get the message/chatter history for a lead or opportunity.

        Args:
            lead_id: ID of the crm.lead record.
            limit: Maximum number of messages to return.
        """
        client: OdooClient = await get_client()
        return await client.search_read(
            "mail.message",
            [("res_id", "=", lead_id), ("model", "=", "crm.lead")],
            ["id", "author_id", "body", "message_type", "subtype_id", "date"],
            limit=limit,
            order="date desc",
        )


async def _get_crm_lead_model_id(client: OdooClient) -> int:
    """Get the ir.model id for crm.lead."""
    records = await client.search_read(
        "ir.model", [("model", "=", "crm.lead")], ["id"], limit=1
    )
    if not records:
        raise ValueError("crm.lead model not found in ir.model")
    return records[0]["id"]
