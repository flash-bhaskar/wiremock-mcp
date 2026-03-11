"""MCP tool definitions for persona switching.

All tools return structured responses in the format:
    { "success": bool, "data": ..., "error": str | None, "metadata": dict }
"""

import logging
from typing import Any

from fastmcp import Context

from wiremock_mcp.services.persona_service import PersonaService

logger = logging.getLogger(__name__)


def _ok(data: Any, **metadata: Any) -> dict:
    """Build a successful response envelope."""
    return {"success": True, "data": data, "error": None, "metadata": metadata}


def _err(error: str, **metadata: Any) -> dict:
    """Build an error response envelope."""
    return {"success": False, "data": None, "error": error, "metadata": metadata}


def register_persona_tools(mcp: Any, get_persona_service: Any) -> None:
    """Register all persona management tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
        get_persona_service: Callable that returns PersonaService from context.
    """

    @mcp.tool()
    async def list_services(ctx: Context) -> dict:
        """List all services that have persona configurations available.

        Returns the names of all services (e.g. credit_bureau, yes_bank,
        payment_gateway, sim_binding) that have pre-configured test personas.
        Use this to discover what services you can configure.
        """
        try:
            service: PersonaService = get_persona_service(ctx)
            services = service.list_services()
            return _ok(services, total=len(services))
        except Exception as exc:
            logger.exception("list_services failed")
            return _err(str(exc))

    @mcp.tool()
    async def list_personas(ctx: Context, service: str) -> dict:
        """List all available personas for a given service.

        Shows persona names and their descriptions. Use this to see what
        test scenarios are available for a service before activating one.

        Args:
            service: The service name (e.g. "credit_bureau", "yes_bank",
                     "payment_gateway", "sim_binding").
        """
        try:
            svc: PersonaService = get_persona_service(ctx)
            personas = svc.list_personas(service)
            if not personas:
                return _err(
                    f"No personas found for service '{service}'. "
                    f"Available services: {', '.join(svc.list_services())}"
                )
            return _ok(personas, service=service, total=len(personas))
        except Exception as exc:
            logger.exception("list_personas failed")
            return _err(str(exc))

    @mcp.tool()
    async def activate_persona(ctx: Context, service: str, persona: str) -> dict:
        """Activate a persona for a service in WireMock.

        This switches a service's mock behavior by:
        1. Removing any existing stubs for the service
        2. Creating the new persona's stub mapping

        This operation is idempotent — safe to call multiple times.

        Examples:
          - activate_persona("credit_bureau", "new_to_credit")
          - activate_persona("yes_bank", "card_blocked")
          - activate_persona("payment_gateway", "payment_failure")

        Args:
            service: The service name (e.g. "credit_bureau").
            persona: The persona name (e.g. "new_to_credit", "score_750_plus").
        """
        try:
            svc: PersonaService = get_persona_service(ctx)
            result = await svc.activate_persona(service, persona)
            return _ok(result, service=service, persona=persona)
        except Exception as exc:
            logger.exception("activate_persona failed")
            return _err(str(exc))

    @mcp.tool()
    async def activate_multiple_personas(
        ctx: Context,
        activations: list[dict[str, str]],
    ) -> dict:
        """Activate multiple personas at once for a complete test scenario.

        Pass a list of service/persona pairs to configure all services in
        one call. Great for setting up a full test scenario like:
        "credit bureau shows overdues AND payment gateway returns failure"

        Args:
            activations: List of {"service": "...", "persona": "..."} objects.
                Example: [
                    {"service": "credit_bureau", "persona": "has_overdues"},
                    {"service": "payment_gateway", "persona": "payment_failure"},
                    {"service": "yes_bank", "persona": "card_blocked"}
                ]
        """
        try:
            svc: PersonaService = get_persona_service(ctx)
            result = await svc.activate_multiple(activations)
            return _ok(result)
        except Exception as exc:
            logger.exception("activate_multiple_personas failed")
            return _err(str(exc))

    @mcp.tool()
    async def get_current_stubs_for_service(ctx: Context, service: str) -> dict:
        """Show what stubs are currently active for a given service.

        Returns all WireMock stubs whose name starts with the service prefix.
        Use this to verify what persona is currently configured for a service.

        Args:
            service: The service name (e.g. "credit_bureau", "yes_bank").
        """
        try:
            svc: PersonaService = get_persona_service(ctx)
            stubs = await svc.get_current_stubs_for_service(service)
            return _ok(stubs, service=service, total=len(stubs))
        except Exception as exc:
            logger.exception("get_current_stubs_for_service failed")
            return _err(str(exc))
