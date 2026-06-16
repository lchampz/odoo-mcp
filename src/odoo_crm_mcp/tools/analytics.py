"""MCP tools for CRM analytics, pipeline reports, and KPI dashboards."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import OdooClient


def register_analytics_tools(mcp: FastMCP, get_client):
    """Register all analytics and reporting tools."""

    @mcp.tool()
    async def get_pipeline_summary(
        team_id: int | None = None,
        user_id: int | None = None,
    ) -> dict:
        """Get a high-level pipeline summary with stage breakdown, lead counts, and revenue totals.

        Args:
            team_id: Scope to a specific sales team. None = all teams.
            user_id: Scope to a specific salesperson. None = all users.
        """
        client: OdooClient = await get_client()
        domain: list[Any] = [("active", "=", True), ("type", "=", "opportunity")]
        if team_id:
            domain.append(("team_id", "=", team_id))
        if user_id:
            domain.append(("user_id", "=", user_id))

        stages = await client.search_read(
            "crm.stage", [], ["id", "name", "sequence", "is_won"], limit=50, order="sequence asc"
        )

        stage_data = []
        total_leads = 0
        total_revenue = 0.0
        total_prorated = 0.0

        for stage in stages:
            stage_domain = domain + [("stage_id", "=", stage["id"])]
            leads = await client.search_read(
                "crm.lead",
                stage_domain,
                ["id", "expected_revenue", "probability", "prorated_revenue"],
                limit=500,
            )
            count = len(leads)
            revenue = sum(l.get("expected_revenue") or 0 for l in leads)
            prorated = sum(
                (l.get("expected_revenue") or 0) * (l.get("probability") or 0) / 100
                for l in leads
            )
            total_leads += count
            total_revenue += revenue
            total_prorated += prorated
            stage_data.append({
                "stage_id": stage["id"],
                "stage_name": stage["name"],
                "is_won": stage["is_won"],
                "leads_count": count,
                "total_expected_revenue": round(revenue, 2),
                "total_prorated_revenue": round(prorated, 2),
            })

        new_leads_count = await client.search_count(
            "crm.lead",
            [("type", "=", "lead"), ("active", "=", True)]
            + ([("team_id", "=", team_id)] if team_id else [])
            + ([("user_id", "=", user_id)] if user_id else []),
        )

        return {
            "new_leads": new_leads_count,
            "opportunities_count": total_leads,
            "total_expected_revenue": round(total_revenue, 2),
            "total_prorated_revenue": round(total_prorated, 2),
            "by_stage": stage_data,
        }

    @mcp.tool()
    async def get_won_lost_analysis(
        date_from: str | None = None,
        date_to: str | None = None,
        team_id: int | None = None,
        user_id: int | None = None,
    ) -> dict:
        """Analyze won vs. lost opportunities over a time period.

        Args:
            date_from: Start date in YYYY-MM-DD format. Defaults to first day of current month.
            date_to: End date in YYYY-MM-DD format. Defaults to today.
            team_id: Scope to a specific sales team.
            user_id: Scope to a specific salesperson.
        """
        from datetime import date

        client: OdooClient = await get_client()
        today = date.today()

        if not date_from:
            date_from = today.replace(day=1).isoformat()
        if not date_to:
            date_to = today.isoformat()

        base_domain: list[Any] = [
            ("date_closed", ">=", date_from),
            ("date_closed", "<=", date_to),
        ]
        if team_id:
            base_domain.append(("team_id", "=", team_id))
        if user_id:
            base_domain.append(("user_id", "=", user_id))

        won_domain = base_domain + [("active", "=", True), ("probability", "=", 100)]
        lost_domain = base_domain + [("active", "=", False)]

        won_leads = await client.search_read(
            "crm.lead", won_domain, ["id", "expected_revenue", "user_id", "team_id"], limit=500
        )
        lost_leads = await client.search_read(
            "crm.lead", lost_domain, ["id", "expected_revenue", "lost_reason_id", "user_id", "team_id"], limit=500
        )

        lost_by_reason: dict[str, dict] = {}
        for l in lost_leads:
            reason = l.get("lost_reason_id")
            reason_name = reason[1] if reason else "No reason specified"
            if reason_name not in lost_by_reason:
                lost_by_reason[reason_name] = {"count": 0, "revenue": 0.0}
            lost_by_reason[reason_name]["count"] += 1
            lost_by_reason[reason_name]["revenue"] += l.get("expected_revenue") or 0

        return {
            "period": {"from": date_from, "to": date_to},
            "won": {
                "count": len(won_leads),
                "total_revenue": round(sum(l.get("expected_revenue") or 0 for l in won_leads), 2),
            },
            "lost": {
                "count": len(lost_leads),
                "total_revenue": round(sum(l.get("expected_revenue") or 0 for l in lost_leads), 2),
                "by_reason": lost_by_reason,
            },
            "win_rate_percent": round(
                len(won_leads) / (len(won_leads) + len(lost_leads)) * 100
                if (won_leads or lost_leads) else 0,
                1,
            ),
        }

    @mcp.tool()
    async def get_salesperson_performance(
        date_from: str | None = None,
        date_to: str | None = None,
        team_id: int | None = None,
    ) -> list[dict]:
        """Get performance breakdown by salesperson (won deals, pipeline, revenue).

        Args:
            date_from: Period start (YYYY-MM-DD). Defaults to first day of current month.
            date_to: Period end (YYYY-MM-DD). Defaults to today.
            team_id: Scope to a specific team.
        """
        from datetime import date

        client: OdooClient = await get_client()
        today = date.today()
        if not date_from:
            date_from = today.replace(day=1).isoformat()
        if not date_to:
            date_to = today.isoformat()

        base_domain: list[Any] = []
        if team_id:
            base_domain.append(("team_id", "=", team_id))

        all_opps = await client.search_read(
            "crm.lead",
            base_domain + [("type", "=", "opportunity")],
            ["id", "user_id", "expected_revenue", "probability", "active", "date_closed"],
            limit=2000,
        )

        perf: dict[int, dict] = {}
        for opp in all_opps:
            uid_tuple = opp.get("user_id")
            if not uid_tuple:
                continue
            uid, uname = uid_tuple[0], uid_tuple[1]
            if uid not in perf:
                perf[uid] = {
                    "user_id": uid,
                    "user_name": uname,
                    "pipeline_count": 0,
                    "pipeline_revenue": 0.0,
                    "won_count": 0,
                    "won_revenue": 0.0,
                    "lost_count": 0,
                }
            rev = opp.get("expected_revenue") or 0
            prob = opp.get("probability") or 0
            is_active = opp.get("active", True)
            dc = opp.get("date_closed")

            if is_active and prob < 100:
                perf[uid]["pipeline_count"] += 1
                perf[uid]["pipeline_revenue"] += rev
            elif prob == 100 and dc and date_from <= dc[:10] <= date_to:
                perf[uid]["won_count"] += 1
                perf[uid]["won_revenue"] += rev
            elif not is_active:
                perf[uid]["lost_count"] += 1

        result = sorted(perf.values(), key=lambda x: x["won_revenue"], reverse=True)
        for r in result:
            r["pipeline_revenue"] = round(r["pipeline_revenue"], 2)
            r["won_revenue"] = round(r["won_revenue"], 2)
        return result

    @mcp.tool()
    async def get_leads_by_source() -> list[dict]:
        """Get lead counts grouped by traffic source (UTM source)."""
        client: OdooClient = await get_client()
        leads = await client.search_read(
            "crm.lead",
            [("active", "=", True)],
            ["id", "source_id", "type", "expected_revenue"],
            limit=5000,
        )
        grouped: dict[str, dict] = {}
        for lead in leads:
            src = lead.get("source_id")
            key = src[1] if src else "Direct / Unknown"
            if key not in grouped:
                grouped[key] = {"source": key, "leads": 0, "opportunities": 0, "revenue": 0.0}
            if lead["type"] == "lead":
                grouped[key]["leads"] += 1
            else:
                grouped[key]["opportunities"] += 1
                grouped[key]["revenue"] += lead.get("expected_revenue") or 0

        result = sorted(grouped.values(), key=lambda x: x["opportunities"] + x["leads"], reverse=True)
        for r in result:
            r["revenue"] = round(r["revenue"], 2)
        return result

    @mcp.tool()
    async def get_overdue_opportunities(team_id: int | None = None, user_id: int | None = None) -> list[dict]:
        """List all opportunities with a passed deadline (overdue).

        Args:
            team_id: Scope to a specific team.
            user_id: Scope to a specific salesperson.
        """
        from datetime import date

        client: OdooClient = await get_client()
        domain: list[Any] = [
            ("type", "=", "opportunity"),
            ("active", "=", True),
            ("date_deadline", "<", date.today().isoformat()),
            ("probability", "<", 100),
        ]
        if team_id:
            domain.append(("team_id", "=", team_id))
        if user_id:
            domain.append(("user_id", "=", user_id))

        return await client.search_read(
            "crm.lead",
            domain,
            ["id", "name", "partner_id", "user_id", "team_id", "stage_id",
             "expected_revenue", "date_deadline", "priority"],
            limit=200,
            order="date_deadline asc",
        )

    @mcp.tool()
    async def get_pipeline_forecast(months_ahead: int = 3, team_id: int | None = None) -> list[dict]:
        """Forecast expected revenue from the pipeline grouped by closing month.

        Args:
            months_ahead: Number of future months to forecast (1-12).
            team_id: Scope to a specific team.
        """
        from datetime import date

        client: OdooClient = await get_client()
        today = date.today()
        domain: list[Any] = [
            ("type", "=", "opportunity"),
            ("active", "=", True),
            ("date_deadline", ">=", today.isoformat()),
            ("probability", ">", 0),
            ("probability", "<", 100),
        ]
        if team_id:
            domain.append(("team_id", "=", team_id))

        leads = await client.search_read(
            "crm.lead",
            domain,
            ["id", "name", "expected_revenue", "probability", "date_deadline"],
            limit=2000,
        )

        monthly: dict[str, dict] = {}
        for lead in leads:
            dd = lead.get("date_deadline")
            if not dd:
                continue
            month_key = dd[:7]
            if month_key not in monthly:
                monthly[month_key] = {"month": month_key, "count": 0, "expected": 0.0, "weighted": 0.0}
            rev = lead.get("expected_revenue") or 0
            prob = lead.get("probability") or 0
            monthly[month_key]["count"] += 1
            monthly[month_key]["expected"] += rev
            monthly[month_key]["weighted"] += rev * prob / 100

        result = sorted(monthly.values(), key=lambda x: x["month"])[:months_ahead]
        for r in result:
            r["expected"] = round(r["expected"], 2)
            r["weighted"] = round(r["weighted"], 2)
        return result

    @mcp.tool()
    async def get_conversion_funnel(team_id: int | None = None) -> dict:
        """Get the lead-to-close conversion funnel: Leads → Opportunities → Won.

        Args:
            team_id: Scope to a specific team.
        """
        client: OdooClient = await get_client()
        base: list[Any] = [("active", "=", True)] + ([("team_id", "=", team_id)] if team_id else [])

        total_leads = await client.search_count("crm.lead", base + [("type", "=", "lead")])
        total_opps = await client.search_count("crm.lead", base + [("type", "=", "opportunity")])
        won_opps = await client.search_count(
            "crm.lead", base + [("type", "=", "opportunity"), ("probability", "=", 100)]
        )

        return {
            "leads": total_leads,
            "opportunities": total_opps,
            "won": won_opps,
            "lead_to_opp_rate": round(total_opps / total_leads * 100, 1) if total_leads else 0,
            "opp_to_won_rate": round(won_opps / total_opps * 100, 1) if total_opps else 0,
            "overall_rate": round(won_opps / total_leads * 100, 1) if total_leads else 0,
        }

    @mcp.tool()
    async def get_leads_created_this_week(team_id: int | None = None) -> dict:
        """Count new leads and opportunities created in the last 7 days.

        Args:
            team_id: Scope to a specific team.
        """
        from datetime import date, timedelta

        client: OdooClient = await get_client()
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        base: list[Any] = [
            ("create_date", ">=", week_ago),
        ]
        if team_id:
            base.append(("team_id", "=", team_id))

        leads = await client.search_count("crm.lead", base + [("type", "=", "lead")])
        opps = await client.search_count("crm.lead", base + [("type", "=", "opportunity")])

        return {
            "since": week_ago,
            "new_leads": leads,
            "new_opportunities": opps,
            "total": leads + opps,
        }
