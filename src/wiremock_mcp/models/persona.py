"""Pydantic models for persona management."""

from pydantic import BaseModel

from wiremock_mcp.models.stub import StubMapping


class PersonaStub(BaseModel):
    """A persona-linked stub mapping.

    Associates a WireMock stub mapping with a service and persona name,
    along with a human-readable description.
    """

    service: str
    persona_name: str
    description: str
    stub_mapping: StubMapping


class PersonaLibrary(BaseModel):
    """Complete persona library indexed by service and persona name.

    Structure: { service_name: { persona_name: PersonaStub } }
    """

    personas: dict[str, dict[str, PersonaStub]]

    @property
    def services(self) -> list[str]:
        """List all available service names."""
        return sorted(self.personas.keys())

    def get_personas_for_service(self, service: str) -> dict[str, PersonaStub]:
        """Get all personas for a given service."""
        return self.personas.get(service, {})

    def get_persona(self, service: str, persona_name: str) -> PersonaStub | None:
        """Get a specific persona by service and name."""
        return self.personas.get(service, {}).get(persona_name)
