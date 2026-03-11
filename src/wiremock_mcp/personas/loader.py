"""Persona loader that auto-discovers persona JSON files from disk."""

import json
import logging
from pathlib import Path

from wiremock_mcp.models.persona import PersonaLibrary, PersonaStub
from wiremock_mcp.models.stub import StubMapping

logger = logging.getLogger(__name__)


class PersonaLoader:
    """Loads persona stub definitions from a directory of JSON files.

    Directory structure expected:
        library/
        ├── credit_bureau/
        │   ├── new_to_credit.json
        │   └── score_750_plus.json
        └── yes_bank/
            ├── card_activate_success.json
            └── card_blocked.json

    Each JSON file must be a valid WireMock stub mapping. The service
    name comes from the directory name, and the persona name from the
    file name (without .json extension). Adding a new JSON file in a
    service directory automatically makes it available.
    """

    def __init__(self, library_dir: Path) -> None:
        self._library_dir = library_dir

    def load(self) -> PersonaLibrary:
        """Load all personas from the library directory.

        Returns:
            A PersonaLibrary containing all discovered personas.
        """
        personas: dict[str, dict[str, PersonaStub]] = {}

        if not self._library_dir.exists():
            logger.warning("Personas directory does not exist: %s", self._library_dir)
            return PersonaLibrary(personas={})

        for service_dir in sorted(self._library_dir.iterdir()):
            if not service_dir.is_dir() or service_dir.name.startswith("."):
                continue

            service_name = service_dir.name
            personas[service_name] = {}

            for persona_file in sorted(service_dir.glob("*.json")):
                try:
                    persona_name = persona_file.stem
                    persona_stub = self._load_persona_file(
                        service_name, persona_name, persona_file
                    )
                    personas[service_name][persona_name] = persona_stub
                    logger.debug(
                        "Loaded persona: %s/%s", service_name, persona_name
                    )
                except Exception:
                    logger.exception(
                        "Failed to load persona file: %s", persona_file
                    )

        total = sum(len(p) for p in personas.values())
        logger.info(
            "Loaded %d personas across %d services from %s",
            total, len(personas), self._library_dir,
        )
        return PersonaLibrary(personas=personas)

    def _load_persona_file(
        self, service: str, persona_name: str, path: Path
    ) -> PersonaStub:
        """Load a single persona from a JSON file."""
        with open(path) as f:
            data = json.load(f)

        stub_mapping = StubMapping.model_validate(data)

        description = self._generate_description(service, persona_name, data)

        return PersonaStub(
            service=service,
            persona_name=persona_name,
            description=description,
            stub_mapping=stub_mapping,
        )

    def _generate_description(
        self, service: str, persona_name: str, data: dict
    ) -> str:
        """Generate a human-readable description for a persona.

        Uses the stub name if available, otherwise constructs from
        service and persona name.
        """
        if "description" in data:
            return data["description"]

        readable_name = persona_name.replace("_", " ").replace("-", " ").title()
        readable_service = service.replace("_", " ").replace("-", " ").title()

        response = data.get("response", {})
        status = response.get("status", "?")
        json_body = response.get("jsonBody", {})

        if isinstance(json_body, dict) and "status" in json_body:
            return f"{readable_service} - {readable_name} (HTTP {status}, {json_body['status']})"

        return f"{readable_service} - {readable_name} (HTTP {status})"
