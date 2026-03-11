"""MCP tool definitions for WireMock diagnostics and debugging.

All tools return structured responses in the format:
    { "success": bool, "data": ..., "error": str | None, "metadata": dict }
"""

import logging
from typing import Any

from fastmcp import Context

from wiremock_mcp.repositories.stub_repository import WireMockStubRepository
from wiremock_mcp.services.stub_service import StubService

logger = logging.getLogger(__name__)


def _ok(data: Any, **metadata: Any) -> dict:
    """Build a successful response envelope."""
    return {"success": True, "data": data, "error": None, "metadata": metadata}


def _err(error: str, **metadata: Any) -> dict:
    """Build an error response envelope."""
    return {"success": False, "data": None, "error": error, "metadata": metadata}


def register_diagnostic_tools(
    mcp: Any,
    get_stub_service: Any,
    get_repository: Any,
    get_http_client: Any,
) -> None:
    """Register all diagnostic tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
        get_stub_service: Callable that returns StubService from context.
        get_repository: Callable that returns WireMockStubRepository from context.
        get_http_client: Callable that returns the HTTP client from context.
    """

    @mcp.tool()
    async def get_recent_requests(ctx: Context, limit: int = 25) -> dict:
        """Get recent requests received by WireMock.

        Shows the last N requests with their matched/unmatched status.
        Useful for verifying that your application is hitting the right
        endpoints and that stubs are matching correctly.

        Args:
            limit: Maximum number of requests to return (default 25).
        """
        try:
            service: StubService = get_stub_service(ctx)
            requests = await service.get_requests(limit)
            summary = [
                {
                    "id": r.id,
                    "method": r.method,
                    "url": r.url,
                    "timestamp": r.logged_date_string,
                    "was_matched": r.was_matched,
                }
                for r in requests
            ]
            return _ok(summary, total=len(summary), limit=limit)
        except Exception as exc:
            logger.exception("get_recent_requests failed")
            return _err(str(exc))

    @mcp.tool()
    async def get_unmatched_requests(ctx: Context) -> dict:
        """Get requests that did not match any WireMock stub.

        These are requests that WireMock received but had no matching stub
        for, so they returned a default 404. Use this to find missing stubs
        that need to be created for your test scenario.
        """
        try:
            service: StubService = get_stub_service(ctx)
            requests = await service.get_unmatched_requests()
            summary = [
                {
                    "id": r.id,
                    "method": r.method,
                    "url": r.url,
                    "timestamp": r.logged_date_string,
                    "body_preview": r.body[:200] if r.body else None,
                }
                for r in requests
            ]
            return _ok(summary, total=len(summary))
        except Exception as exc:
            logger.exception("get_unmatched_requests failed")
            return _err(str(exc))

    @mcp.tool()
    async def find_stubs_for_url(ctx: Context, url: str) -> dict:
        """Find which WireMock stubs would match a given URL.

        Checks all configured stubs against the provided URL using the
        same matching logic WireMock uses (exact match, path match,
        regex pattern match). Useful for debugging why a request matched
        or didn't match a specific stub.

        Args:
            url: The URL path to check (e.g. "/api/credit-report/v1/fetch").
        """
        try:
            repo: WireMockStubRepository = get_repository(ctx)
            stubs = await repo.find_stubs_by_url(url)
            summary = [
                {
                    "id": s.id,
                    "name": s.name,
                    "method": s.request.method,
                    "priority": s.priority,
                    "url_matcher": (
                        s.request.url
                        or s.request.url_pattern
                        or s.request.url_path
                        or s.request.url_path_pattern
                    ),
                    "response_status": s.response.status,
                }
                for s in stubs
            ]
            return _ok(summary, url=url, total=len(summary))
        except Exception as exc:
            logger.exception("find_stubs_for_url failed")
            return _err(str(exc))

    @mcp.tool()
    async def get_wiremock_health(ctx: Context) -> dict:
        """Check WireMock server health and version.

        Pings the WireMock admin API to verify it is running and reachable.
        Returns the server version and status. Use this to diagnose
        connectivity issues.
        """
        try:
            from wiremock_mcp.client.base import AbstractHttpClient
            client: AbstractHttpClient = get_http_client(ctx)
            # WireMock exposes /__admin as the root admin endpoint
            data = await client.get("")
            return _ok({
                "status": "healthy",
                "wiremock_info": data,
            })
        except Exception as exc:
            logger.exception("get_wiremock_health failed")
            return _err(f"WireMock health check failed: {exc}")

    @mcp.tool()
    async def get_request_count(
        ctx: Context,
        url_pattern: str,
        method: str | None = None,
    ) -> dict:
        """Count requests matching a URL pattern since last reset.

        Returns the number of requests WireMock received that match the
        given URL regex pattern. Useful for verifying that expected API
        calls were made during a test.

        Args:
            url_pattern: Regex pattern to match request URLs (e.g. "/api/credit.*").
            method: Optional HTTP method filter (e.g. "POST").
        """
        try:
            repo: WireMockStubRepository = get_repository(ctx)
            count = await repo.count_requests_by_url(url_pattern, method)
            return _ok(
                {"count": count},
                url_pattern=url_pattern,
                method=method,
            )
        except Exception as exc:
            logger.exception("get_request_count failed")
            return _err(str(exc))
