"""Custom exceptions for the WireMock MCP server."""


class WireMockMCPError(Exception):
    """Base exception for all WireMock MCP errors."""


class WireMockConnectionError(WireMockMCPError):
    """Raised when connection to WireMock fails."""

    def __init__(self, message: str = "Failed to connect to WireMock server"):
        super().__init__(message)


class WireMockApiError(WireMockMCPError):
    """Raised when WireMock API returns an unexpected error."""

    def __init__(self, status_code: int, message: str = "WireMock API error"):
        self.status_code = status_code
        super().__init__(f"{message} (HTTP {status_code})")


class WireMockStubNotFoundError(WireMockMCPError):
    """Raised when a requested stub mapping is not found."""

    def __init__(self, stub_id: str):
        self.stub_id = stub_id
        super().__init__(f"Stub mapping not found: {stub_id}")


class PersonaNotFoundError(WireMockMCPError):
    """Raised when a requested persona is not found."""

    def __init__(self, service: str, persona: str):
        self.service = service
        self.persona = persona
        super().__init__(f"Persona not found: {service}/{persona}")
