"""Abstract HTTP client interface (Dependency Inversion Principle)."""

from abc import ABC, abstractmethod
from typing import Any


class AbstractHttpClient(ABC):
    """Abstract interface for HTTP operations.

    Concrete implementations can use httpx, aiohttp, or any other
    async HTTP library. This allows swapping the HTTP layer without
    affecting business logic.
    """

    @abstractmethod
    async def get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform an HTTP GET request.

        Args:
            url: The URL to request.
            params: Optional query parameters.

        Returns:
            Parsed JSON response as a dictionary.
        """

    @abstractmethod
    async def post(self, url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform an HTTP POST request.

        Args:
            url: The URL to request.
            body: Optional JSON body.

        Returns:
            Parsed JSON response as a dictionary.
        """

    @abstractmethod
    async def put(self, url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform an HTTP PUT request.

        Args:
            url: The URL to request.
            body: Optional JSON body.

        Returns:
            Parsed JSON response as a dictionary.
        """

    @abstractmethod
    async def delete(self, url: str) -> bool:
        """Perform an HTTP DELETE request.

        Args:
            url: The URL to request.

        Returns:
            True if deletion was successful.
        """
