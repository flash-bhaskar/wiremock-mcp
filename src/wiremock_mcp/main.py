"""WireMock MCP Server entrypoint.

Initializes the FastMCP server, registers all tools, and manages the
httpx client lifecycle via a lifespan context manager.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastmcp import Context, FastMCP

from wiremock_mcp.client.wiremock_client import WireMockHttpClient
from wiremock_mcp.config import Settings, get_settings
from wiremock_mcp.personas.loader import PersonaLoader
from wiremock_mcp.repositories.stub_repository import WireMockStubRepository
from wiremock_mcp.services.persona_service import PersonaService
from wiremock_mcp.services.stub_service import StubService
from wiremock_mcp.tools.diagnostic_tools import register_diagnostic_tools
from wiremock_mcp.tools.persona_tools import register_persona_tools
from wiremock_mcp.tools.stub_tools import register_stub_tools


@dataclass
class AppContext:
    """Shared application context available to all tools."""

    http_client: WireMockHttpClient
    repository: WireMockStubRepository
    stub_service: StubService
    persona_service: PersonaService
    settings: Settings


def _configure_logging(level: str) -> None:
    """Configure structured logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def _build_app_context(settings: Settings) -> AppContext:
    """Build the full dependency graph."""
    http_client = WireMockHttpClient(
        base_url=settings.admin_url,
        timeout=settings.wiremock_timeout_seconds,
        verify_ssl=settings.wiremock_verify_ssl,
    )
    repository = WireMockStubRepository(client=http_client)
    stub_service = StubService(repository=repository)

    loader = PersonaLoader(settings.personas_path)
    library = loader.load()

    persona_service = PersonaService(
        library=library,
        stub_service=stub_service,
    )

    return AppContext(
        http_client=http_client,
        repository=repository,
        stub_service=stub_service,
        persona_service=persona_service,
        settings=settings,
    )


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle.

    Creates the httpx client and all services on startup,
    and ensures proper cleanup on shutdown.
    """
    settings = get_settings()
    _configure_logging(settings.log_level)
    logger = logging.getLogger(__name__)

    logger.info("Starting WireMock MCP Server")
    logger.info("WireMock URL: %s", settings.wiremock_base_url)
    logger.info("Admin API: %s", settings.admin_url)
    logger.info("Personas directory: %s", settings.personas_path)

    app_ctx = _build_app_context(settings)

    persona_count = sum(
        len(personas)
        for personas in app_ctx.persona_service._library.personas.values()
    )
    service_count = len(app_ctx.persona_service.list_services())
    logger.info(
        "Loaded %d personas across %d services",
        persona_count,
        service_count,
    )
    logger.info("Tools registered: stub (10), persona (5), diagnostic (5)")
    logger.info("WireMock MCP Server ready")

    try:
        yield app_ctx
    finally:
        await app_ctx.http_client.close()
        logger.info("WireMock MCP Server shutdown complete")


def _get_app_ctx(ctx: Context) -> AppContext:
    """Extract AppContext from FastMCP context."""
    return ctx.request_context.lifespan_context


def _get_stub_service(ctx: Context) -> StubService:
    return _get_app_ctx(ctx).stub_service


def _get_persona_service(ctx: Context) -> PersonaService:
    return _get_app_ctx(ctx).persona_service


def _get_repository(ctx: Context) -> WireMockStubRepository:
    return _get_app_ctx(ctx).repository


def _get_http_client(ctx: Context) -> WireMockHttpClient:
    return _get_app_ctx(ctx).http_client


mcp = FastMCP(
    "WireMock Zet QA",
    lifespan=lifespan,
)

# Register all tools
register_stub_tools(mcp, _get_stub_service)
register_persona_tools(mcp, _get_persona_service)
register_diagnostic_tools(mcp, _get_stub_service, _get_repository, _get_http_client)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
