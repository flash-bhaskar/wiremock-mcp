"""MCP tool definitions for WireMock stub management.

All tools return structured responses in the format:
    { "success": bool, "data": ..., "error": str | None, "metadata": dict }
"""

import logging
from typing import Any

from fastmcp import Context

from wiremock_mcp.models.stub import (
    PostServeAction,
    RequestPattern,
    ResponseDefinition,
    StubMapping,
    WebhookParameters,
)
from wiremock_mcp.services.stub_service import StubService

logger = logging.getLogger(__name__)


def _ok(data: Any, **metadata: Any) -> dict:
    """Build a successful response envelope."""
    return {"success": True, "data": data, "error": None, "metadata": metadata}


def _err(error: str, **metadata: Any) -> dict:
    """Build an error response envelope."""
    return {"success": False, "data": None, "error": error, "metadata": metadata}


def register_stub_tools(mcp: Any, get_stub_service: Any) -> None:
    """Register all stub management tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
        get_stub_service: Callable that returns the StubService from context.
    """

    @mcp.tool()
    async def list_stubs(ctx: Context) -> dict:
        """List all WireMock stub mappings.

        Returns a summary of every stub configured in WireMock, including
        each stub's ID, name, HTTP method, and URL pattern. Use this to
        get an overview of what stubs are currently active.
        """
        try:
            service: StubService = get_stub_service(ctx)
            stubs = await service.list_stubs()
            summary = []
            for s in stubs:
                summary.append({
                    "id": s.id,
                    "name": s.name,
                    "method": s.request.method,
                    "url": (
                        s.request.url
                        or s.request.url_pattern
                        or s.request.url_path
                        or s.request.url_path_pattern
                    ),
                    "priority": s.priority,
                    "response_status": s.response.status,
                })
            return _ok(summary, total=len(summary))
        except Exception as exc:
            logger.exception("list_stubs failed")
            return _err(str(exc))

    @mcp.tool()
    async def get_stub(ctx: Context, stub_id: str) -> dict:
        """Get the full details of a WireMock stub mapping by its ID.

        Returns the complete request matching pattern and response definition
        including headers, body patterns, delays, and scenario configuration.

        Args:
            stub_id: The UUID of the stub mapping to retrieve.
        """
        try:
            service: StubService = get_stub_service(ctx)
            stub = await service.get_stub(stub_id)
            if stub is None:
                return _err(f"Stub not found: {stub_id}")
            return _ok(stub.model_dump(by_alias=True, exclude_none=True))
        except Exception as exc:
            logger.exception("get_stub failed")
            return _err(str(exc))

    @mcp.tool()
    async def create_stub(
        ctx: Context,
        method: str,
        url: str | None = None,
        url_pattern: str | None = None,
        url_path: str | None = None,
        url_path_pattern: str | None = None,
        name: str | None = None,
        priority: int | None = None,
        response_status: int = 200,
        response_headers: dict[str, str] | None = None,
        response_json_body: Any = None,
        response_body: str | None = None,
        fixed_delay_ms: int | None = None,
        body_patterns: list[dict[str, Any]] | None = None,
        header_matchers: dict[str, Any] | None = None,
        query_parameters: dict[str, Any] | None = None,
        scenario_name: str | None = None,
        webhook_url: str | None = None,
        webhook_method: str | None = None,
        webhook_headers: dict[str, str] | None = None,
        webhook_body: str | None = None,
    ) -> dict:
        """Create a new WireMock stub mapping.

        Configures WireMock to return a specific response when an incoming
        request matches the defined criteria. You must provide at least one
        URL matching parameter (url, url_pattern, url_path, or url_path_pattern).

        Args:
            method: HTTP method to match (GET, POST, PUT, DELETE, etc.).
            url: Exact URL to match (e.g. "/api/users/123").
            url_pattern: Regex URL pattern to match (e.g. "/api/users/.*").
            url_path: URL path prefix to match.
            url_path_pattern: Regex URL path pattern to match.
            name: Human-readable name for this stub.
            priority: Matching priority (lower number = higher priority).
            response_status: HTTP status code to return (default 200).
            response_headers: Response headers as key-value pairs.
            response_json_body: JSON body to return (dict or list).
            response_body: Plain text body to return.
            fixed_delay_ms: Fixed delay in milliseconds before responding.
            body_patterns: Request body matching patterns (list of dicts with keys like "contains", "equalToJson").
            header_matchers: Request header matching criteria.
            query_parameters: Query parameter matching criteria.
            scenario_name: Scenario name for stateful behavior.
            webhook_url: URL to send a webhook callback to after the stub responds.
            webhook_method: HTTP method for the webhook (default POST).
            webhook_headers: Headers to include in the webhook request.
            webhook_body: Body to send in the webhook request.
        """
        try:
            service: StubService = get_stub_service(ctx)

            from wiremock_mcp.models.stub import BodyPattern, StringMatchPattern

            parsed_body_patterns = None
            if body_patterns:
                parsed_body_patterns = [BodyPattern.model_validate(bp) for bp in body_patterns]

            parsed_headers = None
            if header_matchers:
                parsed_headers = {
                    k: StringMatchPattern.model_validate(v) if isinstance(v, dict) else v
                    for k, v in header_matchers.items()
                }

            parsed_qp = None
            if query_parameters:
                parsed_qp = {
                    k: StringMatchPattern.model_validate(v) if isinstance(v, dict) else v
                    for k, v in query_parameters.items()
                }

            request = RequestPattern(
                method=method,
                url=url,
                urlPattern=url_pattern,
                urlPath=url_path,
                urlPathPattern=url_path_pattern,
                headers=parsed_headers,
                queryParameters=parsed_qp,
                bodyPatterns=parsed_body_patterns,
            )
            response = ResponseDefinition(
                status=response_status,
                headers=response_headers,
                jsonBody=response_json_body,
                body=response_body,
                fixedDelayMilliseconds=fixed_delay_ms,
            )
            post_serve_actions = None
            if webhook_url:
                post_serve_actions = [
                    PostServeAction(
                        name="webhook",
                        parameters=WebhookParameters(
                            method=webhook_method or "POST",
                            url=webhook_url,
                            headers=webhook_headers,
                            body=webhook_body,
                        ),
                    )
                ]

            stub = StubMapping(
                name=name,
                priority=priority,
                request=request,
                response=response,
                postServeActions=post_serve_actions,
                scenarioName=scenario_name,
            )
            created = await service.create_stub(stub)
            return _ok(
                created.model_dump(by_alias=True, exclude_none=True),
                stub_id=created.id,
            )
        except Exception as exc:
            logger.exception("create_stub failed")
            return _err(str(exc))

    @mcp.tool()
    async def update_stub(
        ctx: Context,
        stub_id: str,
        method: str | None = None,
        url: str | None = None,
        url_pattern: str | None = None,
        url_path: str | None = None,
        url_path_pattern: str | None = None,
        name: str | None = None,
        priority: int | None = None,
        response_status: int | None = None,
        response_headers: dict[str, str] | None = None,
        response_json_body: Any = None,
        response_body: str | None = None,
        fixed_delay_ms: int | None = None,
        body_patterns: list[dict[str, Any]] | None = None,
        webhook_url: str | None = None,
        webhook_method: str | None = None,
        webhook_headers: dict[str, str] | None = None,
        webhook_body: str | None = None,
    ) -> dict:
        """Update an existing WireMock stub mapping.

        Replaces the stub configuration for the given ID. You should first
        use get_stub to see the current configuration, then provide the
        updated values. All fields of the stub will be replaced.

        Args:
            stub_id: The UUID of the stub to update.
            method: HTTP method to match.
            url: Exact URL to match.
            url_pattern: Regex URL pattern to match.
            url_path: URL path prefix to match.
            url_path_pattern: Regex URL path pattern to match.
            name: Human-readable name for this stub.
            priority: Matching priority.
            response_status: HTTP status code to return.
            response_headers: Response headers.
            response_json_body: JSON body to return.
            response_body: Plain text body to return.
            fixed_delay_ms: Fixed delay in milliseconds.
            body_patterns: Request body matching patterns.
            webhook_url: URL to send a webhook callback to after the stub responds.
            webhook_method: HTTP method for the webhook (default POST).
            webhook_headers: Headers to include in the webhook request.
            webhook_body: Body to send in the webhook request.
        """
        try:
            service: StubService = get_stub_service(ctx)

            existing = await service.get_stub(stub_id)
            if existing is None:
                return _err(f"Stub not found: {stub_id}")

            from wiremock_mcp.models.stub import BodyPattern

            parsed_body_patterns = None
            if body_patterns:
                parsed_body_patterns = [BodyPattern.model_validate(bp) for bp in body_patterns]

            request = RequestPattern(
                method=method or existing.request.method,
                url=url or existing.request.url,
                urlPattern=url_pattern or existing.request.url_pattern,
                urlPath=url_path or existing.request.url_path,
                urlPathPattern=url_path_pattern or existing.request.url_path_pattern,
                headers=existing.request.headers,
                queryParameters=existing.request.query_parameters,
                bodyPatterns=parsed_body_patterns or existing.request.body_patterns,
            )
            response = ResponseDefinition(
                status=response_status if response_status is not None else existing.response.status,
                headers=response_headers or existing.response.headers,
                jsonBody=response_json_body if response_json_body is not None else existing.response.json_body,
                body=response_body or existing.response.body,
                fixedDelayMilliseconds=fixed_delay_ms or existing.response.fixed_delay_milliseconds,
            )
            post_serve_actions = existing.post_serve_actions
            if webhook_url:
                post_serve_actions = [
                    PostServeAction(
                        name="webhook",
                        parameters=WebhookParameters(
                            method=webhook_method or "POST",
                            url=webhook_url,
                            headers=webhook_headers,
                            body=webhook_body,
                        ),
                    )
                ]

            stub = StubMapping(
                name=name or existing.name,
                priority=priority or existing.priority,
                request=request,
                response=response,
                postServeActions=post_serve_actions,
                scenarioName=existing.scenario_name,
            )
            updated = await service.update_stub(stub_id, stub)
            return _ok(
                updated.model_dump(by_alias=True, exclude_none=True),
                stub_id=stub_id,
            )
        except Exception as exc:
            logger.exception("update_stub failed")
            return _err(str(exc))

    @mcp.tool()
    async def delete_stub(ctx: Context, stub_id: str) -> dict:
        """Delete a WireMock stub mapping by its ID.

        Permanently removes the stub from WireMock. This cannot be undone.
        Use list_stubs or get_stub first to verify you have the right stub.

        Args:
            stub_id: The UUID of the stub to delete.
        """
        try:
            service: StubService = get_stub_service(ctx)
            result = await service.delete_stub(stub_id)
            return _ok({"deleted": result}, stub_id=stub_id)
        except Exception as exc:
            logger.exception("delete_stub failed")
            return _err(str(exc))

    @mcp.tool()
    async def search_stubs(ctx: Context, name_contains: str) -> dict:
        """Search WireMock stubs by name substring.

        Finds all stubs whose name contains the given text (case-insensitive).
        Useful for finding stubs for a specific service or feature.

        Args:
            name_contains: Text to search for in stub names.
        """
        try:
            service: StubService = get_stub_service(ctx)
            stubs = await service.search_stubs(name_contains)
            summary = [
                {
                    "id": s.id,
                    "name": s.name,
                    "method": s.request.method,
                    "url": (
                        s.request.url
                        or s.request.url_pattern
                        or s.request.url_path
                        or s.request.url_path_pattern
                    ),
                }
                for s in stubs
            ]
            return _ok(summary, total=len(summary), query=name_contains)
        except Exception as exc:
            logger.exception("search_stubs failed")
            return _err(str(exc))

    @mcp.tool()
    async def reset_stubs(ctx: Context, confirmed: bool = False) -> dict:
        """Reset all WireMock stubs to their default state.

        WARNING: This removes ALL custom stub mappings. This action cannot
        be undone. You must pass confirmed=True to proceed.

        Args:
            confirmed: Safety flag — must be True to actually perform the reset.
        """
        try:
            if not confirmed:
                return _err(
                    "Reset not confirmed. Pass confirmed=True to reset all stubs. "
                    "This will remove ALL custom mappings."
                )
            service: StubService = get_stub_service(ctx)
            result = await service.reset()
            return _ok({"reset": result})
        except Exception as exc:
            logger.exception("reset_stubs failed")
            return _err(str(exc))

    @mcp.tool()
    async def add_webhook_to_stub(
        ctx: Context,
        stub_id: str,
        webhook_url: str,
        webhook_method: str = "POST",
        webhook_headers: dict[str, str] | None = None,
        webhook_body: str | None = None,
    ) -> dict:
        """Add a webhook (postServeAction) to an existing WireMock stub.

        Fetches the stub, appends the webhook to its postServeActions list,
        and updates the stub. Multiple webhooks can be added to the same stub.

        Args:
            stub_id: The UUID of the stub to add the webhook to.
            webhook_url: URL to send the webhook callback to.
            webhook_method: HTTP method for the webhook (default POST).
            webhook_headers: Headers to include in the webhook request.
            webhook_body: Body to send in the webhook request.
        """
        try:
            service: StubService = get_stub_service(ctx)

            existing = await service.get_stub(stub_id)
            if existing is None:
                return _err(f"Stub not found: {stub_id}")

            new_action = PostServeAction(
                name="webhook",
                parameters=WebhookParameters(
                    method=webhook_method,
                    url=webhook_url,
                    headers=webhook_headers,
                    body=webhook_body,
                ),
            )
            actions = list(existing.post_serve_actions or [])
            actions.append(new_action)
            existing.post_serve_actions = actions

            updated = await service.update_stub(stub_id, existing)
            return _ok(
                updated.model_dump(by_alias=True, exclude_none=True),
                stub_id=stub_id,
                webhooks_count=len(updated.post_serve_actions or []),
            )
        except Exception as exc:
            logger.exception("add_webhook_to_stub failed")
            return _err(str(exc))

    @mcp.tool()
    async def remove_webhooks_from_stub(ctx: Context, stub_id: str) -> dict:
        """Remove all webhooks (postServeActions) from a WireMock stub.

        Fetches the stub, clears its postServeActions list, and updates it.

        Args:
            stub_id: The UUID of the stub to remove webhooks from.
        """
        try:
            service: StubService = get_stub_service(ctx)

            existing = await service.get_stub(stub_id)
            if existing is None:
                return _err(f"Stub not found: {stub_id}")

            removed_count = len(existing.post_serve_actions or [])
            existing.post_serve_actions = None

            updated = await service.update_stub(stub_id, existing)
            return _ok(
                updated.model_dump(by_alias=True, exclude_none=True),
                stub_id=stub_id,
                webhooks_removed=removed_count,
            )
        except Exception as exc:
            logger.exception("remove_webhooks_from_stub failed")
            return _err(str(exc))

    @mcp.tool()
    async def bulk_create_stubs(
        ctx: Context,
        stubs: list[dict[str, Any]],
    ) -> dict:
        """Create multiple WireMock stubs at once.

        Each item in the stubs list should be a complete WireMock stub mapping
        with 'request' and 'response' objects. Use this for setting up a full
        test scenario with many stubs in one call.

        Args:
            stubs: List of WireMock stub mapping objects, each containing
                   'request' and 'response' definitions.
        """
        try:
            service: StubService = get_stub_service(ctx)
            stub_models = [StubMapping.model_validate(s) for s in stubs]
            created = await service.bulk_import(stub_models)
            summary = [
                {"id": s.id, "name": s.name}
                for s in created
            ]
            return _ok(
                summary,
                total_requested=len(stubs),
                total_created=len(created),
            )
        except Exception as exc:
            logger.exception("bulk_create_stubs failed")
            return _err(str(exc))
