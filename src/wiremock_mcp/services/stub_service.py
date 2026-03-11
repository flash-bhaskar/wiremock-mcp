"""Business logic service for WireMock stub CRUD operations."""

import logging

from wiremock_mcp.models.stub import RecordedRequest, StubMapping
from wiremock_mcp.repositories.base import AbstractStubRepository

logger = logging.getLogger(__name__)


class StubService:
    """Stub management service.

    Encapsulates business logic for stub CRUD operations, search,
    bulk import, and request inspection. Delegates persistence to
    the injected repository.
    """

    def __init__(self, repository: AbstractStubRepository) -> None:
        self._repo = repository

    async def list_stubs(self) -> list[StubMapping]:
        """List all stub mappings."""
        return await self._repo.list_stubs()

    async def get_stub(self, stub_id: str) -> StubMapping | None:
        """Get a single stub mapping by ID."""
        return await self._repo.get_stub(stub_id)

    async def create_stub(self, stub: StubMapping) -> StubMapping:
        """Create a new stub mapping."""
        return await self._repo.create_stub(stub)

    async def update_stub(self, stub_id: str, stub: StubMapping) -> StubMapping:
        """Update an existing stub mapping by ID."""
        return await self._repo.update_stub(stub_id, stub)

    async def delete_stub(self, stub_id: str) -> bool:
        """Delete a stub mapping by ID."""
        return await self._repo.delete_stub(stub_id)

    async def search_stubs(self, name_contains: str) -> list[StubMapping]:
        """Search stubs by name substring (case-insensitive)."""
        all_stubs = await self._repo.list_stubs()
        query = name_contains.lower()
        return [
            s for s in all_stubs
            if s.name and query in s.name.lower()
        ]

    async def reset(self) -> bool:
        """Reset all stub mappings to defaults."""
        return await self._repo.reset()

    async def bulk_import(self, stubs: list[StubMapping]) -> list[StubMapping]:
        """Create multiple stubs at once.

        Returns the list of created stubs. Continues on individual failures
        and logs errors.
        """
        created: list[StubMapping] = []
        for stub in stubs:
            try:
                result = await self._repo.create_stub(stub)
                created.append(result)
            except Exception:
                logger.exception("Failed to create stub: %s", stub.name)
        return created

    async def get_requests(self, limit: int = 50) -> list[RecordedRequest]:
        """Get recent recorded requests."""
        return await self._repo.get_requests(limit)

    async def get_unmatched_requests(self) -> list[RecordedRequest]:
        """Get requests that did not match any stub."""
        return await self._repo.get_unmatched_requests()
