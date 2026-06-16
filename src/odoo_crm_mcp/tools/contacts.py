"""MCP tools for res.partner — contact and customer management (CRM context)."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import OdooClient

PARTNER_FIELDS = [
    "id", "name", "type", "company_type", "company_id", "parent_id",
    "email", "phone", "mobile", "website", "street", "city",
    "state_id", "country_id", "zip", "vat", "lang",
    "customer_rank", "supplier_rank", "active",
    "opportunity_ids", "activity_ids", "category_id",
]

PARTNER_FIELDS_BRIEF = [
    "id", "name", "company_type", "company_id", "email", "phone",
    "mobile", "city", "country_id", "customer_rank", "active",
]


def register_contact_tools(mcp: FastMCP, get_client):
    """Register all contact-related MCP tools."""

    @mcp.tool()
    async def search_contacts(
        query: str,
        is_company: bool | None = None,
        country_id: int | None = None,
        limit: int = 30,
    ) -> list[dict]:
        """Search for contacts/customers by name, email, or phone.

        Args:
            query: Search string matched against name, email, or phone.
            is_company: True to return only companies, False for individuals, None for both.
            country_id: Filter by country (res.country ID).
            limit: Maximum results.
        """
        client: OdooClient = await get_client()
        domain: list[Any] = [
            "|", "|",
            ("name", "ilike", query),
            ("email", "ilike", query),
            ("phone", "ilike", query),
            ("active", "=", True),
        ]
        if is_company is not None:
            domain.append(("is_company", "=", is_company))
        if country_id:
            domain.append(("country_id", "=", country_id))

        return await client.search_read("res.partner", domain, PARTNER_FIELDS_BRIEF, limit)

    @mcp.tool()
    async def get_contact(partner_id: int) -> dict:
        """Get full details of a contact or company.

        Args:
            partner_id: The res.partner record ID.
        """
        client: OdooClient = await get_client()
        records = await client.read("res.partner", [partner_id], PARTNER_FIELDS)
        if not records:
            raise ValueError(f"Partner {partner_id} not found")
        return records[0]

    @mcp.tool()
    async def create_contact(
        name: str,
        is_company: bool = False,
        company_id: int | None = None,
        email: str | None = None,
        phone: str | None = None,
        mobile: str | None = None,
        street: str | None = None,
        city: str | None = None,
        state_id: int | None = None,
        zip: str | None = None,
        country_id: int | None = None,
        website: str | None = None,
        vat: str | None = None,
        lang: str = "pt_BR",
    ) -> dict:
        """Create a new contact or company in Odoo.

        Args:
            name: Contact or company name.
            is_company: True to create as a company, False for an individual.
            company_id: Parent company ID if this is an individual contact.
            email: Email address.
            phone: Phone number.
            mobile: Mobile number.
            street: Street address.
            city: City.
            state_id: State/province ID (res.country.state).
            zip: Postal/ZIP code.
            country_id: Country ID (res.country).
            website: Website URL.
            vat: Tax ID / VAT number.
            lang: Language code (e.g. 'pt_BR', 'en_US').
        """
        client: OdooClient = await get_client()
        values: dict[str, Any] = {"name": name, "is_company": is_company, "lang": lang}
        optional = {
            "company_id": company_id, "email": email, "phone": phone, "mobile": mobile,
            "street": street, "city": city, "state_id": state_id, "zip": zip,
            "country_id": country_id, "website": website, "vat": vat,
        }
        for k, v in optional.items():
            if v is not None:
                values[k] = v

        pid = await client.create("res.partner", values)
        records = await client.read("res.partner", [pid], PARTNER_FIELDS)
        return records[0]

    @mcp.tool()
    async def update_contact(
        partner_id: int,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        mobile: str | None = None,
        street: str | None = None,
        city: str | None = None,
        state_id: int | None = None,
        zip: str | None = None,
        country_id: int | None = None,
        website: str | None = None,
        vat: str | None = None,
        company_id: int | None = None,
    ) -> dict:
        """Update an existing contact or company.

        Args:
            partner_id: The res.partner record ID to update.
            name: New name.
            email: New email.
            phone: New phone.
            mobile: New mobile.
            street: Street address.
            city: City.
            state_id: State ID.
            zip: Postal code.
            country_id: Country ID.
            website: Website URL.
            vat: Tax / VAT number.
            company_id: Parent company ID.
        """
        client: OdooClient = await get_client()
        values: dict[str, Any] = {}
        optional = {
            "name": name, "email": email, "phone": phone, "mobile": mobile,
            "street": street, "city": city, "state_id": state_id, "zip": zip,
            "country_id": country_id, "website": website, "vat": vat, "company_id": company_id,
        }
        for k, v in optional.items():
            if v is not None:
                values[k] = v
        if not values:
            raise ValueError("No fields to update")
        await client.write("res.partner", [partner_id], values)
        records = await client.read("res.partner", [partner_id], PARTNER_FIELDS)
        return records[0]

    @mcp.tool()
    async def get_contact_opportunities(partner_id: int) -> list[dict]:
        """Get all CRM opportunities linked to a contact or company.

        Args:
            partner_id: The res.partner record ID.
        """
        client: OdooClient = await get_client()
        return await client.search_read(
            "crm.lead",
            [("partner_id", "=", partner_id)],
            ["id", "name", "type", "stage_id", "user_id", "expected_revenue",
             "probability", "date_deadline", "active"],
            limit=100,
        )

    @mcp.tool()
    async def list_countries() -> list[dict]:
        """List all countries available in Odoo for address fields."""
        client: OdooClient = await get_client()
        return await client.search_read(
            "res.country", [], ["id", "name", "code"], limit=300, order="name asc"
        )

    @mcp.tool()
    async def list_states(country_id: int) -> list[dict]:
        """List all states/provinces for a given country.

        Args:
            country_id: The res.country record ID.
        """
        client: OdooClient = await get_client()
        return await client.search_read(
            "res.country.state",
            [("country_id", "=", country_id)],
            ["id", "name", "code"],
            limit=200,
            order="name asc",
        )
