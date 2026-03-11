"""Pydantic models for WireMock stub mappings and recorded requests."""

from typing import Any

from pydantic import BaseModel, Field


class BodyPattern(BaseModel):
    """A body matching pattern for WireMock request matching.

    Supports multiple match strategies: exact, contains, regex, JSON equality.
    """

    contains: str | None = None
    equal_to: str | None = Field(default=None, alias="equalTo")
    matches: str | None = None
    does_not_match: str | None = Field(default=None, alias="doesNotMatch")
    equal_to_json: Any | None = Field(default=None, alias="equalToJson")
    match_type: str | None = Field(default=None, alias="matchType")
    case_insensitive: bool | None = Field(default=None, alias="caseInsensitive")

    model_config = {"populate_by_name": True}


class StringMatchPattern(BaseModel):
    """A string matching pattern used in headers and query parameters."""

    equal_to: str | None = Field(default=None, alias="equalTo")
    contains: str | None = None
    matches: str | None = None
    does_not_match: str | None = Field(default=None, alias="doesNotMatch")
    case_insensitive: bool | None = Field(default=None, alias="caseInsensitive")

    model_config = {"populate_by_name": True}


class RequestPattern(BaseModel):
    """WireMock request matching pattern.

    Defines the criteria for matching incoming requests to a stub.
    Supports URL matching (exact, pattern, path), method, headers,
    query parameters, and body patterns.
    """

    method: str | None = None
    url: str | None = None
    url_pattern: str | None = Field(default=None, alias="urlPattern")
    url_path: str | None = Field(default=None, alias="urlPath")
    url_path_pattern: str | None = Field(default=None, alias="urlPathPattern")
    headers: dict[str, StringMatchPattern | str] | None = None
    query_parameters: dict[str, StringMatchPattern | str] | None = Field(
        default=None, alias="queryParameters"
    )
    body_patterns: list[BodyPattern] | None = Field(
        default=None, alias="bodyPatterns"
    )

    model_config = {"populate_by_name": True}


class ResponseDefinition(BaseModel):
    """WireMock response definition.

    Defines what response WireMock should return when a request matches.
    Supports static bodies, JSON bodies, file references, delays, and faults.
    """

    status: int = 200
    status_message: str | None = Field(default=None, alias="statusMessage")
    headers: dict[str, str] | None = None
    json_body: Any | None = Field(default=None, alias="jsonBody")
    body: str | None = None
    body_file_name: str | None = Field(default=None, alias="bodyFileName")
    base64_body: str | None = Field(default=None, alias="base64Body")
    fixed_delay_milliseconds: int | None = Field(
        default=None, alias="fixedDelayMilliseconds"
    )
    delay_distribution: dict[str, Any] | None = Field(
        default=None, alias="delayDistribution"
    )
    fault: str | None = None
    transformers: list[str] | None = None

    model_config = {"populate_by_name": True}


class WebhookParameters(BaseModel):
    """Parameters for a webhook HTTP callback.

    Defines the HTTP request WireMock will fire after a stub matches.
    """

    method: str = "POST"
    url: str
    headers: dict[str, str] | None = None
    body: str | None = None
    delay: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class PostServeAction(BaseModel):
    """A post-serve action (e.g. webhook) attached to a stub.

    WireMock fires these after sending the stub response.
    """

    name: str = "webhook"
    parameters: WebhookParameters

    model_config = {"populate_by_name": True}


class StubMapping(BaseModel):
    """A complete WireMock stub mapping.

    Represents a request-response pair configured in WireMock.
    Each mapping has a unique ID, optional name, priority, and
    optional scenario state for stateful behavior.
    """

    id: str | None = None
    uuid: str | None = None
    name: str | None = None
    priority: int | None = None
    request: RequestPattern
    response: ResponseDefinition
    post_serve_actions: list[PostServeAction] | None = Field(
        default=None, alias="postServeActions"
    )
    scenario_name: str | None = Field(default=None, alias="scenarioName")
    required_scenario_state: str | None = Field(
        default=None, alias="requiredScenarioState"
    )
    new_scenario_state: str | None = Field(
        default=None, alias="newScenarioState"
    )
    persistent: bool | None = None
    metadata: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class RecordedRequest(BaseModel):
    """A request recorded by WireMock.

    Represents a request that was received by WireMock, including
    whether it matched a stub or not.
    """

    id: str | None = None
    url: str | None = None
    absolute_url: str | None = Field(default=None, alias="absoluteUrl")
    method: str | None = None
    headers: dict[str, Any] | None = None
    body: str | None = None
    logged_date: int | None = Field(default=None, alias="loggedDate")
    logged_date_string: str | None = Field(
        default=None, alias="loggedDateString"
    )
    was_matched: bool | None = Field(default=None, alias="wasMatched")

    model_config = {"populate_by_name": True}
