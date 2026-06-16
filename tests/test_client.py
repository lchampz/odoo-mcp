"""Unit tests for OdooClient using httpx mocking."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from odoo_crm_mcp.client import OdooClient, OdooError


@pytest.fixture
def client():
    return OdooClient(
        url="https://test.odoo.com",
        database="test_db",
        username="admin@test.com",
        password="secret",
    )


@pytest.mark.asyncio
async def test_authenticate_success(client):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"jsonrpc": "2.0", "result": 1, "id": 1})

    with patch.object(client._client, "post", new=AsyncMock(return_value=mock_response)):
        uid = await client.authenticate()
        assert uid == 1
        assert client.uid == 1


@pytest.mark.asyncio
async def test_authenticate_failure(client):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"jsonrpc": "2.0", "result": False, "id": 1})

    with patch.object(client._client, "post", new=AsyncMock(return_value=mock_response)):
        with pytest.raises(OdooError, match="Authentication failed"):
            await client.authenticate()


@pytest.mark.asyncio
async def test_jsonrpc_error_response(client):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "jsonrpc": "2.0",
        "error": {
            "code": 200,
            "message": "Odoo Server Error",
            "data": {"message": "Record not found"},
        },
        "id": 1,
    })

    with patch.object(client._client, "post", new=AsyncMock(return_value=mock_response)):
        with pytest.raises(OdooError, match="Record not found"):
            await client._jsonrpc("/web/dataset/call_kw")


@pytest.mark.asyncio
async def test_search_read(client):
    client.uid = 1
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "jsonrpc": "2.0",
        "result": [{"id": 1, "name": "Test Lead"}],
        "id": 1,
    })

    with patch.object(client._client, "post", new=AsyncMock(return_value=mock_response)):
        result = await client.search_read("crm.lead", [], ["id", "name"])
        assert len(result) == 1
        assert result[0]["name"] == "Test Lead"


@pytest.mark.asyncio
async def test_create(client):
    client.uid = 1
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"jsonrpc": "2.0", "result": 42, "id": 1})

    with patch.object(client._client, "post", new=AsyncMock(return_value=mock_response)):
        result = await client.create("crm.lead", {"name": "New Lead"})
        assert result == 42


@pytest.mark.asyncio
async def test_url_trailing_slash_stripped():
    client = OdooClient("https://test.odoo.com/", "db", "user", "pass")
    assert client.url == "https://test.odoo.com"
