"""Business logic service for persona switching."""

import logging

from wiremock_mcp.exceptions import PersonaNotFoundError
from wiremock_mcp.models.persona import PersonaLibrary, PersonaStub
from wiremock_mcp.services.stub_service import StubService

logger = logging.getLogger(__name__)


class PersonaService:
    """Persona management service.

    Handles listing, activating, and switching personas. A persona
    is a pre-configured WireMock stub for a specific service, identified
    by a service/persona name pair. Activation is idempotent — existing
    stubs for the service are removed before the new persona stub is created.
    """

    def __init__(self, library: PersonaLibrary, stub_service: StubService) -> None:
        self._library = library
        self._stub_service = stub_service

    def list_services(self) -> list[str]:
        """List all available service names in the persona library."""
        return self._library.services

    def list_personas(self, service: str) -> list[dict[str, str]]:
        """List all personas for a given service with descriptions."""
        personas = self._library.get_personas_for_service(service)
        return [
            {"name": name, "description": p.description}
            for name, p in sorted(personas.items())
        ]

    def get_persona(self, service: str, persona: str) -> PersonaStub | None:
        """Get a specific persona by service and name."""
        return self._library.get_persona(service, persona)

    async def activate_persona(self, service: str, persona: str) -> dict:
        """Activate a persona for a service.

        This operation is idempotent:
        1. Finds and deletes all existing stubs whose name starts with
           the service prefix (e.g. 'credit-bureau-').
        2. Creates the new stub from the persona library.
        3. Returns an activation summary.

        Args:
            service: The service name (e.g. 'credit_bureau').
            persona: The persona name (e.g. 'new_to_credit').

        Returns:
            Dict with activation summary including deleted and created stubs.

        Raises:
            PersonaNotFoundError: If the service/persona combination doesn't exist.
        """
        persona_stub = self._library.get_persona(service, persona)
        if persona_stub is None:
            raise PersonaNotFoundError(service, persona)

        service_prefix = service.replace("_", "-") + "-"

        # Find and delete existing stubs for this service
        all_stubs = await self._stub_service.list_stubs()
        deleted_ids: list[str] = []
        for stub in all_stubs:
            if stub.name and stub.name.startswith(service_prefix):
                if stub.id:
                    await self._stub_service.delete_stub(stub.id)
                    deleted_ids.append(stub.id)

        # Create the new persona stub
        created = await self._stub_service.create_stub(persona_stub.stub_mapping)

        logger.info(
            "Activated persona %s/%s: deleted %d stubs, created %s",
            service, persona, len(deleted_ids), created.id,
        )

        return {
            "service": service,
            "persona": persona,
            "description": persona_stub.description,
            "deleted_stubs": deleted_ids,
            "created_stub_id": created.id,
            "stub_name": created.name,
        }

    async def activate_multiple(self, activations: list[dict[str, str]]) -> dict:
        """Activate multiple personas at once.

        Args:
            activations: List of dicts with 'service' and 'persona' keys.

        Returns:
            Dict with results for each activation and overall summary.
        """
        results: list[dict] = []
        errors: list[dict] = []

        for activation in activations:
            service = activation["service"]
            persona = activation["persona"]
            try:
                result = await self.activate_persona(service, persona)
                results.append(result)
            except Exception as exc:
                logger.exception("Failed to activate %s/%s", service, persona)
                errors.append({
                    "service": service,
                    "persona": persona,
                    "error": str(exc),
                })

        return {
            "activated": results,
            "errors": errors,
            "total_activated": len(results),
            "total_errors": len(errors),
        }

    async def get_current_stubs_for_service(self, service: str) -> list[dict]:
        """Get all currently active stubs for a service.

        Finds stubs whose name starts with the service prefix.
        """
        service_prefix = service.replace("_", "-") + "-"
        all_stubs = await self._stub_service.list_stubs()
        matching = []
        for stub in all_stubs:
            if stub.name and stub.name.startswith(service_prefix):
                matching.append({
                    "id": stub.id,
                    "name": stub.name,
                    "method": stub.request.method,
                    "url": (
                        stub.request.url
                        or stub.request.url_pattern
                        or stub.request.url_path
                        or stub.request.url_path_pattern
                    ),
                    "status": stub.response.status,
                })
        return matching
