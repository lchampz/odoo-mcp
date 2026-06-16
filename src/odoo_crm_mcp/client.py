"""Odoo JSON-RPC client with session authentication and connection pooling."""

import json
import logging
from typing import Any
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)


class OdooError(Exception):
    """Raised when Odoo returns an error response."""

    def __init__(self, message: str, code: int | None = None, data: Any = None):
        super().__init__(message)
        self.code = code
        self.data = data


class OdooClient:
    """Async Odoo JSON-RPC client with automatic session management."""

    def __init__(self, url: str, database: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.database = database
        self.username = username
        self.password = password
        self.uid: int | None = None
        self._client = httpx.AsyncClient(timeout=60.0)

    async def __aenter__(self):
        await self.authenticate()
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()

    async def authenticate(self) -> int:
        """Authenticate with Odoo and cache the uid."""
        result = await self._jsonrpc(
            "/web/dataset/call_kw",
            method="call",
            params={
                "model": "res.users",
                "method": "authenticate",
                "args": [self.database, self.username, self.password, {}],
                "kwargs": {},
            },
        )
        if not result or not isinstance(result, int):
            raise OdooError("Authentication failed — check credentials and database name")
        self.uid = result
        logger.info("Authenticated as uid=%d on %s", self.uid, self.database)
        return self.uid

    async def _jsonrpc(self, endpoint: str, method: str = "call", params: dict | None = None) -> Any:
        """Low-level JSON-RPC call."""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": 1,
            "params": params or {},
        }
        response = await self._client.post(
            urljoin(self.url, endpoint),
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            err = data["error"]
            msg = err.get("data", {}).get("message", err.get("message", "Unknown error"))
            raise OdooError(msg, code=err.get("code"), data=err.get("data"))

        return data.get("result")

    async def execute_kw(
        self,
        model: str,
        method: str,
        args: list,
        kwargs: dict | None = None,
    ) -> Any:
        """Call model method via execute_kw (the standard Odoo RPC entrypoint)."""
        if self.uid is None:
            await self.authenticate()

        return await self._jsonrpc(
            "/web/dataset/call_kw",
            params={
                "model": model,
                "method": method,
                "args": args,
                "kwargs": kwargs or {},
            },
        )

    # ── Convenience wrappers ────────────────────────────────────────────────

    async def search_read(
        self,
        model: str,
        domain: list,
        fields: list[str],
        limit: int = 80,
        offset: int = 0,
        order: str | None = None,
    ) -> list[dict]:
        kwargs: dict[str, Any] = {"fields": fields, "limit": limit, "offset": offset}
        if order:
            kwargs["order"] = order
        return await self.execute_kw(model, "search_read", [domain], kwargs)

    async def create(self, model: str, values: dict) -> int:
        return await self.execute_kw(model, "create", [values])

    async def write(self, model: str, ids: list[int], values: dict) -> bool:
        return await self.execute_kw(model, "write", [ids, values])

    async def unlink(self, model: str, ids: list[int]) -> bool:
        return await self.execute_kw(model, "unlink", [ids])

    async def read(self, model: str, ids: list[int], fields: list[str]) -> list[dict]:
        return await self.execute_kw(model, "read", [ids], {"fields": fields})

    async def search(self, model: str, domain: list, limit: int = 80, offset: int = 0) -> list[int]:
        return await self.execute_kw(model, "search", [domain], {"limit": limit, "offset": offset})

    async def search_count(self, model: str, domain: list) -> int:
        return await self.execute_kw(model, "search_count", [domain])

    async def fields_get(self, model: str, attributes: list[str] | None = None) -> dict:
        kwargs = {}
        if attributes:
            kwargs["attributes"] = attributes
        return await self.execute_kw(model, "fields_get", [], kwargs)

    async def call_method(self, model: str, method: str, ids: list[int], **kwargs) -> Any:
        return await self.execute_kw(model, method, [ids], kwargs)
