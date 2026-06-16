# odoo-crm-mcp

An MCP (Model Context Protocol) server for **Odoo CRM** — giving any AI assistant full control over your CRM pipeline via a clean, well-documented tool interface.

[![PyPI](https://img.shields.io/pypi/v/odoo-crm-mcp)](https://pypi.org/project/odoo-crm-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/odoo-crm-mcp)](https://pypi.org/project/odoo-crm-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

| Category | Tools |
|---|---|
| **Leads & Opportunities** | List, search, create, update, delete, archive, convert lead→opportunity, win, lose, bulk update, move stage, assign salesperson |
| **Pipeline Stages** | List, create, update, delete, reorder stages |
| **Sales Teams** | List, create, update, add/remove members, get full team pipeline |
| **Activities** | List types, schedule, list (mine / on lead), mark done, cancel, reschedule |
| **Chatter** | Log internal notes, send messages, get message history |
| **Contacts** | Search, get, create, update contacts/companies, get contact opportunities |
| **Tags** | List, create, update, delete CRM tags |
| **Analytics** | Pipeline summary, won/lost analysis, salesperson performance, leads by source, overdue opportunities, revenue forecast, conversion funnel |
| **Users** | List salespersons, current user info, search users |
| **Utility** | `ping` — test connection and verify Odoo version |

## Quick Start

### 1. Install

```bash
# Using uvx (recommended — no install needed)
uvx odoo-crm-mcp

# Or install globally with pip
pip install odoo-crm-mcp
```

### 2. Configure

Create a `.env` file (or set environment variables):

```env
ODOO_URL=https://your-company.odoo.com
ODOO_DATABASE=your-database-name
ODOO_USERNAME=admin@yourcompany.com
ODOO_PASSWORD=your-api-key-or-password
```

> **Tip:** Use an Odoo API key as the password for better security. You can generate one in Odoo → Settings → Technical → API Keys.

### 3. Add to Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "odoo-crm": {
      "command": "uvx",
      "args": ["odoo-crm-mcp"],
      "env": {
        "ODOO_URL": "https://your-company.odoo.com",
        "ODOO_DATABASE": "your-database-name",
        "ODOO_USERNAME": "admin@yourcompany.com",
        "ODOO_PASSWORD": "your-api-key"
      }
    }
  }
}
```

**Config file locations:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/claude/claude_desktop_config.json`

### 4. Add to Claude Code (CLI)

```bash
claude mcp add odoo-crm \
  -e ODOO_URL=https://your-company.odoo.com \
  -e ODOO_DATABASE=your-database-name \
  -e ODOO_USERNAME=admin@yourcompany.com \
  -e ODOO_PASSWORD=your-api-key \
  -- uvx odoo-crm-mcp
```

Or add manually to `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "odoo-crm": {
      "command": "uvx",
      "args": ["odoo-crm-mcp"],
      "env": {
        "ODOO_URL": "https://your-company.odoo.com",
        "ODOO_DATABASE": "your-database-name",
        "ODOO_USERNAME": "admin@yourcompany.com",
        "ODOO_PASSWORD": "your-api-key"
      }
    }
  }
}
```

### 5. Other MCP clients (Cursor, Windsurf, Continue, etc.)

```json
{
  "mcp": {
    "servers": {
      "odoo-crm": {
        "command": "uvx",
        "args": ["odoo-crm-mcp"],
        "env": {
          "ODOO_URL": "https://your-company.odoo.com",
          "ODOO_DATABASE": "your-database-name",
          "ODOO_USERNAME": "admin@yourcompany.com",
          "ODOO_PASSWORD": "your-api-key"
        }
      }
    }
  }
}
```

## Example Prompts

Once connected, you can ask your AI assistant things like:

```
Show me all opportunities in the pipeline for the Sales Team with total expected revenue.

Create a new lead for Acme Corp, contact John Smith, email john@acme.com, expected revenue $50,000.

Move opportunity #42 to the 'Negotiation' stage and schedule a follow-up call for next Monday.

Show me all overdue opportunities assigned to me.

What's our win rate this month vs last month?

List all leads that came in this week grouped by source.

Mark opportunity #15 as Won.

Who are the top performers by won revenue this quarter?

Show me the revenue forecast for the next 3 months.
```

## Tool Reference

### Leads & Opportunities

| Tool | Description |
|---|---|
| `list_leads` | List leads/opportunities with filters (type, stage, team, salesperson) |
| `search_leads` | Full-text search across name, email, phone, contact |
| `get_lead` | Get full details of a single lead |
| `create_lead` | Create a new lead or opportunity |
| `update_lead` | Update any fields on a lead/opportunity |
| `delete_lead` | Permanently delete a lead |
| `archive_lead` | Soft-delete (archive) a lead |
| `unarchive_lead` | Restore an archived lead |
| `mark_lead_won` | Mark an opportunity as Won |
| `mark_lead_lost` | Mark an opportunity as Lost (with optional reason) |
| `convert_lead_to_opportunity` | Qualify a lead into an opportunity |
| `move_lead_to_stage` | Move a lead to a specific pipeline stage |
| `assign_lead` | Assign a lead to a salesperson and/or team |
| `get_lost_reasons` | Get available lost reason options |
| `bulk_update_leads` | Update multiple leads at once |

### Stages

| Tool | Description |
|---|---|
| `list_stages` | List all pipeline stages |
| `get_stage` | Get details of a specific stage |
| `create_stage` | Create a new pipeline stage |
| `update_stage` | Modify a stage |
| `delete_stage` | Delete a stage (fails if leads exist in it) |
| `reorder_stages` | Reorder stages by setting sequence numbers |

### Sales Teams

| Tool | Description |
|---|---|
| `list_teams` | List all sales teams |
| `get_team` | Get team details |
| `create_team` | Create a new team |
| `update_team` | Update team name/leader/members |
| `add_team_member` | Add a salesperson to a team |
| `remove_team_member` | Remove a salesperson from a team |
| `get_team_pipeline` | Get full pipeline view for a team |

### Activities & Chatter

| Tool | Description |
|---|---|
| `list_activity_types` | List available activity types |
| `schedule_activity` | Schedule an activity on a lead |
| `list_lead_activities` | List activities for a specific lead |
| `list_my_activities` | List the current user's activities |
| `mark_activity_done` | Mark an activity as completed |
| `cancel_activity` | Cancel a scheduled activity |
| `reschedule_activity` | Change an activity's due date |
| `log_note_on_lead` | Add an internal note to a lead's chatter |
| `send_message_on_lead` | Send a message on a lead (notifies followers) |
| `get_lead_messages` | Get the chatter/message history of a lead |

### Contacts

| Tool | Description |
|---|---|
| `search_contacts` | Search for contacts/companies |
| `get_contact` | Get full contact details |
| `create_contact` | Create a new contact or company |
| `update_contact` | Update contact fields |
| `get_contact_opportunities` | Get all CRM opportunities for a contact |
| `list_countries` | List all countries |
| `list_states` | List states/provinces for a country |

### Tags

| Tool | Description |
|---|---|
| `list_tags` | List all CRM tags |
| `create_tag` | Create a new tag |
| `update_tag` | Update a tag |
| `delete_tag` | Delete a tag |

### Analytics & Reports

| Tool | Description |
|---|---|
| `get_pipeline_summary` | Stage-by-stage pipeline overview with revenue totals |
| `get_won_lost_analysis` | Won vs lost comparison for a time period |
| `get_salesperson_performance` | Performance breakdown per salesperson |
| `get_leads_by_source` | Lead counts grouped by UTM source |
| `get_overdue_opportunities` | All opportunities past their deadline |
| `get_pipeline_forecast` | Revenue forecast by closing month |
| `get_conversion_funnel` | Leads → Opportunities → Won funnel rates |
| `get_leads_created_this_week` | New leads/opportunities in last 7 days |

### Users

| Tool | Description |
|---|---|
| `list_salespersons` | List CRM users (optionally by team) |
| `get_current_user` | Get authenticated user's info |
| `search_users` | Search users by name or email |

## Development

```bash
# Clone the repo
git clone https://github.com/yourusername/odoo-crm-mcp
cd odoo-crm-mcp

# Install with dev extras
pip install -e ".[dev]"

# Copy and fill in your .env
cp .env.example .env

# Run the server in development mode
odoo-crm-mcp

# Run tests
pytest
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ODOO_URL` | Yes | Base URL of your Odoo instance |
| `ODOO_DATABASE` | Yes | Database name |
| `ODOO_USERNAME` | Yes | Odoo user login (email) |
| `ODOO_PASSWORD` | Yes | Password or API key |

## Security Notes

- **Use API keys** instead of passwords where possible (Odoo ≥ 14). Generate in Settings → Technical → API Keys.
- The server only makes calls to your own Odoo instance — no data is sent to third parties.
- Run with a dedicated Odoo user with only the CRM permissions your use-case requires.

## Compatibility

- Odoo 14, 15, 16, 17 (Community and Enterprise)
- Odoo.sh and self-hosted
- Python 3.10+

## License

MIT — use freely in commercial and open-source projects.

## Contributing

Issues and PRs are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
