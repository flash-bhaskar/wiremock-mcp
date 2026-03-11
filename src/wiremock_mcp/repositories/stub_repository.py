"""Concrete stub repository implementation using WireMock admin API."""

import logging

from wiremock_mcp.client.base import AbstractHttpClient
from wiremock_mcp.exceptions import WireMockApiError, WireMockStubNotFoundError
from wiremock_mcp.models.stub import RecordedRequest, StubMapping
from wiremock_mcp.repositories.base import AbstractStubRepository

logger = logging.getLogger(__name__)


class WireMockStubRepository(AbstractStubRepository):
    """Repository that persists stubs via the WireMock admin REST API.

    All operations map directly to WireMock's /__admin/mappings endpoints.
    """

    def __init__(self, client: AbstractHttpClient) -> None:
        self._client = client

    async def list_stubs(self) -> list[StubMapping]:
        """List all stub mappings from WireMock."""
        data = await self._client.get("/mappings")
        mappings = data.get("mappings", [])
        return [StubMapping.model_validate(m) for m in mappings]

    async def get_stub(self, stub_id: str) -> StubMapping | None:
        """Get a single stub mapping by ID from WireMock."""
        try:
            data = await self._client.get(f"/mappings/{stub_id}")
            return StubMapping.model_validate(data)
        except WireMockApiError as exc:
            if exc.status_code == 404:
                return None
            raise

    async def create_stub(self, stub: StubMapping) -> StubMapping:
        """Create a new stub mapping in WireMock."""
        payload = stub.model_dump(by_alias=True, exclude_none=True)
        data = await self._client.post("/mappings", body=payload)
        logger.info("Created stub: %s", data.get("id", "unknown"))
        return StubMapping.model_validate(data)

    async def update_stub(self, stub_id: str, stub: StubMapping) -> StubMapping:
        """Update an existing stub mapping in WireMock."""
        existing = await self.get_stub(stub_id)
        if existing is None:
            raise WireMockStubNotFoundError(stub_id)
        payload = stub.model_dump(by_alias=True, exclude_none=True)
        data = await self._client.put(f"/mappings/{stub_id}", body=payload)
        logger.info("Updated stub: %s", stub_id)
        return StubMapping.model_validate(data)

    async def delete_stub(self, stub_id: str) -> bool:
        """Delete a stub mapping from WireMock."""
        existing = await self.get_stub(stub_id)
        if existing is None:
            raise WireMockStubNotFoundError(stub_id)
        result = await self._client.delete(f"/mappings/{stub_id}")
        logger.info("Deleted stub: %s", stub_id)
        return result

    async def reset(self) -> bool:
        """Reset all stub mappings to defaults in WireMock."""
        await self._client.post("/mappings/reset")
        logger.info("Reset all stub mappings")
        return True

    async def get_requests(self, limit: int = 50) -> list[RecordedRequest]:
        """Get recent recorded requests from WireMock."""
        data = await self._client.get("/requests", params={"limit": limit})
        requests_data = data.get("requests", [])
        return [RecordedRequest.model_validate(r) for r in requests_data]

    async def get_unmatched_requests(self) -> list[RecordedRequest]:
        """Get requests that did not match any stub from WireMock."""
        data = await self._client.get("/requests/unmatched")
        requests_data = data.get("requests", [])
        return [RecordedRequest.model_validate(r) for r in requests_data]

    async def count_requests_by_url(self, url_pattern: str, method: str | None = None) -> int:
        """Count requests matching a URL pattern."""
        body: dict = {"urlPattern": url_pattern}
        if method:
            body["method"] = method
        data = await self._client.post("/requests/count", body=body)
        return data.get("count", 0)

    async def find_stubs_by_url(self, url: str) -> list[StubMapping]:
        """Find stubs that would match a given URL."""
        all_stubs = await self.list_stubs()
        matching = []
        for stub in all_stubs:
            req = stub.request
            if req.url and req.url == url:
                matching.append(stub)
            elif req.url_path and url.startswith(req.url_path):
                matching.append(stub)
            elif req.url_pattern:
                import re
                try:
                    if re.search(req.url_pattern, url):
                        matching.append(stub)
                except re.error:
                    pass
            elif req.url_path_pattern:
                import re
                try:
                    if re.search(req.url_path_pattern, url):
                        matching.append(stub)
                except re.error:
                    pass
        return matching
