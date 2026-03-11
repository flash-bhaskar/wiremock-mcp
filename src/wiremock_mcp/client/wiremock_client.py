"""Concrete HTTP client implementation using httpx."""

import logging
from typing import Any

import httpx

from wiremock_mcp.client.base import AbstractHttpClient
from wiremock_mcp.exceptions import WireMockApiError, WireMockConnectionError

logger = logging.getLogger(__name__)


class WireMockHttpClient(AbstractHttpClient):
    """HTTP client for WireMock admin API using httpx.

    Manages an httpx.AsyncClient with configured timeout and SSL settings.
    The client should be created once and reused across requests via the
    lifespan context manager in main.py.
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout),
            verify=verify_ssl,
        )

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._client.aclose()

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Check response status and parse JSON."""
        if response.status_code >= 400:
            logger.error(
                "WireMock API error: %d %s",
                response.status_code,
                response.text[:500],
            )
            raise WireMockApiError(
                status_code=response.status_code,
                message=response.text[:500],
            )
        if not response.content:
            return {}
        return response.json()

    async def get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform an HTTP GET request against WireMock admin API."""
        try:
            response = await self._client.get(url, params=params)
            return self._handle_response(response)
        except httpx.ConnectError as exc:
            raise WireMockConnectionError(
                f"Cannot connect to WireMock at {self._base_url}: {exc}"
            ) from exc

    async def post(self, url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform an HTTP POST request against WireMock admin API."""
        try:
            response = await self._client.post(url, json=body)
            return self._handle_response(response)
        except httpx.ConnectError as exc:
            raise WireMockConnectionError(
                f"Cannot connect to WireMock at {self._base_url}: {exc}"
            ) from exc

    async def put(self, url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform an HTTP PUT request against WireMock admin API."""
        try:
            response = await self._client.put(url, json=body)
            return self._handle_response(response)
        except httpx.ConnectError as exc:
            raise WireMockConnectionError(
                f"Cannot connect to WireMock at {self._base_url}: {exc}"
            ) from exc

    async def delete(self, url: str) -> bool:
        """Perform an HTTP DELETE request against WireMock admin API."""
        try:
            response = await self._client.delete(url)
            if response.status_code >= 400:
                raise WireMockApiError(
                    status_code=response.status_code,
                    message=response.text[:500],
                )
            return True
        except httpx.ConnectError as exc:
            raise WireMockConnectionError(
                f"Cannot connect to WireMock at {self._base_url}: {exc}"
            ) from exc
