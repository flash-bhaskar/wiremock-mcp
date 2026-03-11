"""Abstract stub repository interface (Dependency Inversion Principle)."""

from abc import ABC, abstractmethod

from wiremock_mcp.models.stub import RecordedRequest, StubMapping


class AbstractStubRepository(ABC):
    """Abstract interface for WireMock stub persistence operations.

    Concrete implementations interact with the WireMock admin API
    or any other stub storage backend.
    """

    @abstractmethod
    async def list_stubs(self) -> list[StubMapping]:
        """List all stub mappings."""

    @abstractmethod
    async def get_stub(self, stub_id: str) -> StubMapping | None:
        """Get a single stub mapping by ID."""

    @abstractmethod
    async def create_stub(self, stub: StubMapping) -> StubMapping:
        """Create a new stub mapping."""

    @abstractmethod
    async def update_stub(self, stub_id: str, stub: StubMapping) -> StubMapping:
        """Update an existing stub mapping."""

    @abstractmethod
    async def delete_stub(self, stub_id: str) -> bool:
        """Delete a stub mapping by ID."""

    @abstractmethod
    async def reset(self) -> bool:
        """Reset all stub mappings to defaults."""

    @abstractmethod
    async def get_requests(self, limit: int = 50) -> list[RecordedRequest]:
        """Get recent recorded requests."""

    @abstractmethod
    async def get_unmatched_requests(self) -> list[RecordedRequest]:
        """Get requests that did not match any stub."""
