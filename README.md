# WireMock MCP Server

Production-grade [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that wraps a self-hosted WireMock admin REST API. Built for the Zet fintech engineering team to manage WireMock stubs for QA environment testing.

## Features

- **20 MCP tools** for stub CRUD, webhooks, persona switching, and diagnostics
- **26 pre-configured personas** across 4 services (credit bureau, YES Bank cards, payment gateway, SIM binding)
- **One-command persona activation** — switch a service's mock behavior instantly
- **Multi-persona activation** — configure full test scenarios in a single call
- **Auto-discovery** — drop a JSON file in the personas directory and it's immediately available
- **Clean architecture** — abstract interfaces, dependency injection, SOLID principles

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- A running WireMock instance

### Installation

```bash
# Clone the repository
cd wiremock-mcp

# Install dependencies
uv sync

# Copy and edit environment config
cp .env.example .env
```

### Configuration (.env)

```env
WIREMOCK_BASE_URL=https://wiremock.example.com
WIREMOCK_TIMEOUT_SECONDS=30
WIREMOCK_VERIFY_SSL=true
PERSONAS_DIR=                # Leave empty to use built-in library
LOG_LEVEL=INFO
```

| Variable | Description | Default |
|----------|-------------|---------|
| `WIREMOCK_BASE_URL` | WireMock server URL | `https://wiremock.example.com` |
| `WIREMOCK_TIMEOUT_SECONDS` | HTTP timeout for WireMock API calls | `30` |
| `WIREMOCK_VERIFY_SSL` | Verify SSL certificates | `true` |
| `PERSONAS_DIR` | Path to persona JSON files (empty = built-in) | _(built-in library)_ |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |

### Running

```bash
# Run the MCP server
uv run wiremock-mcp
```

## Connecting to Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "wiremock": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/wiremock-mcp",
        "run", "wiremock-mcp"
      ],
      "env": {
        "WIREMOCK_BASE_URL": "https://wiremock.example.com"
      }
    }
  }
}
```

## Connecting to Cursor

Add to `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "wiremock": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/wiremock-mcp",
        "run", "wiremock-mcp"
      ],
      "env": {
        "WIREMOCK_BASE_URL": "https://wiremock.example.com"
      }
    }
  }
}
```

## Tool Reference

### Stub Management (10 tools)

| Tool | Description |
|------|-------------|
| `list_stubs` | List all WireMock stub mappings with summary (ID, name, method, URL) |
| `get_stub` | Get full stub details by ID |
| `create_stub` | Create a new stub with full request/response configuration (supports webhooks) |
| `update_stub` | Update an existing stub by ID (supports webhooks) |
| `delete_stub` | Delete a stub by ID |
| `search_stubs` | Search stubs by name substring |
| `reset_stubs` | Reset all stubs to defaults (requires `confirmed=True`) |
| `bulk_create_stubs` | Create multiple stubs at once |
| `add_webhook_to_stub` | Add a webhook (postServeAction) to an existing stub |
| `remove_webhooks_from_stub` | Remove all webhooks from a stub |

### Persona Management (5 tools)

| Tool | Description |
|------|-------------|
| `list_services` | List all services with available personas |
| `list_personas` | List personas for a service with descriptions |
| `activate_persona` | Switch a service to a specific persona |
| `activate_multiple_personas` | Activate several personas at once for a full test scenario |
| `get_current_stubs_for_service` | Show what stubs are active for a service |

### Diagnostics (5 tools)

| Tool | Description |
|------|-------------|
| `get_recent_requests` | Last N requests with matched/unmatched status |
| `get_unmatched_requests` | Requests that hit no stub (find missing stubs) |
| `find_stubs_for_url` | Find which stubs would match a given URL |
| `get_wiremock_health` | Ping WireMock, return version and status |
| `get_request_count` | Count requests matching a URL pattern |

## Persona Library

### Credit Bureau (`credit_bureau`)

| Persona | Description | Test ID |
|---------|-------------|---------|
| `new_to_credit` | No credit history, null score | TESTNTC001 |
| `score_750_plus` | Excellent score (780), clean accounts | TESTSCORE750 |
| `score_600_750` | Fair score (660), some late payments | TESTSCORE660 |
| `score_below_600` | Poor score (480), multiple overdues | TESTSCORE480 |
| `has_overdues` | Active overdues, high DPD | TESTOVD001 |
| `has_written_off` | Written-off accounts | TESTWO001 |
| `no_credit_cards` | Only loan accounts | TESTNOCC001 |
| `no_loans` | Only credit card accounts | TESTNOLOAN001 |
| `multiple_enquiries` | Many recent credit enquiries | TESTENQ001 |
| `frozen_file` | Credit file is frozen | TESTFRZ001 |
| `pan_not_found` | PAN not found in bureau | TESTPNF001 |
| `timeout` | 35s timeout simulation | TESTTIMEOUT001 |
| `error_500` | Internal server error | TESTERR500 |

### YES Bank Cards (`yes_bank`)

| Persona | Description | Test ID |
|---------|-------------|---------|
| `card_activate_success` | Card activation succeeds | TESTCARD001 |
| `card_activate_failure` | Card already active error | TESTCARD002 |
| `card_details_success` | Full card details returned | TESTCARD003 |
| `card_blocked` | Card blocked for fraud | TESTCARD004 |
| `timeout` | 35s timeout simulation | TESTCARD_TIMEOUT |

### Payment Gateway (`payment_gateway`)

| Persona | Description | Test ID |
|---------|-------------|---------|
| `payment_success` | Payment processed successfully | TESTPAY001 |
| `payment_failure` | Insufficient funds error | TESTPAY002 |
| `payment_pending` | Payment in processing state | TESTPAY003 |
| `timeout` | 35s timeout simulation | TESTPAY_TIMEOUT |

### SIM Binding (`sim_binding`)

| Persona | Description | Test ID |
|---------|-------------|---------|
| `binding_success` | SIM binding succeeds | TESTSIM001 |
| `binding_failure` | OTP mismatch error | TESTSIM002 |
| `sim_not_registered` | SIM not registered | TESTSIM003 |
| `timeout` | 35s timeout simulation | TESTSIM_TIMEOUT |

## Example Claude Prompts

### Quick persona switch
> "Switch credit bureau to the has_overdues persona"

### Full test scenario setup
> "Set up a test scenario where the credit bureau shows a score below 600, the payment gateway returns failure, and the YES Bank card is blocked"

### Debugging
> "Show me all unmatched requests in WireMock — what stubs are we missing?"

### Stub management
> "List all stubs and find any related to the payment gateway"

### Health check
> "Is WireMock healthy? How many requests have been made to the credit report endpoint?"

### Create custom stubs
> "Create a stub that returns a 503 for POST /api/v1/kyc with a 5 second delay"

### Webhooks
> "Add a webhook to stub abc-123 that POSTs to https://hooks.example.com/notify when the stub matches"

## Webhooks (postServeActions)

WireMock supports webhooks via `postServeActions` — when a stub matches a request, WireMock can fire an HTTP callback to a configured URL.

### Adding webhooks when creating a stub

Use the `webhook_url` parameter (and optionally `webhook_method`, `webhook_headers`, `webhook_body`) with `create_stub` or `update_stub`:

```
create_stub(
  method="POST",
  url="/api/v1/payment",
  response_status=200,
  response_json_body={"status": "SUCCESS"},
  webhook_url="https://hooks.example.com/payment-complete",
  webhook_method="POST",
  webhook_headers={"Authorization": "Bearer token123"},
  webhook_body='{"event": "payment_processed"}'
)
```

### Adding webhooks to existing stubs

Use the `add_webhook_to_stub` tool to append a webhook to any existing stub. Multiple webhooks can be added to the same stub:

```
add_webhook_to_stub(
  stub_id="abc-123",
  webhook_url="https://hooks.example.com/notify",
  webhook_method="POST",
  webhook_body='{"event": "stub_matched"}'
)
```

### Removing webhooks

Use `remove_webhooks_from_stub` to clear all webhooks from a stub:

```
remove_webhooks_from_stub(stub_id="abc-123")
```

### Webhooks in persona JSON files

Persona JSON files can include `postServeActions` and they will be loaded automatically:

```json
{
  "name": "payment-gateway-with-webhook",
  "request": {
    "method": "POST",
    "urlPattern": "/api/v1/payment.*"
  },
  "response": {
    "status": 200,
    "jsonBody": { "status": "SUCCESS" }
  },
  "postServeActions": [
    {
      "name": "webhook",
      "parameters": {
        "method": "POST",
        "url": "https://hooks.example.com/payment-complete",
        "headers": { "Content-Type": "application/json" },
        "body": "{\"event\": \"payment_processed\"}"
      }
    }
  ]
}
```

## Adding New Personas

Drop a JSON file in the appropriate service directory under `src/wiremock_mcp/personas/library/`:

```
personas/library/
├── credit_bureau/
│   └── my_new_persona.json    ← auto-discovered
├── yes_bank/
├── payment_gateway/
└── sim_binding/
```

Each JSON file must be a valid WireMock stub mapping:

```json
{
  "name": "credit-bureau-my-new-persona",
  "priority": 1,
  "request": {
    "method": "POST",
    "urlPattern": "/credit-report/v1/fetch",
    "bodyPatterns": [{ "contains": "TESTNEW001" }]
  },
  "response": {
    "status": 200,
    "headers": { "Content-Type": "application/json" },
    "jsonBody": { "status": "SUCCESS", "score": 800 }
  }
}
```

To add a completely new service, create a new directory and add persona JSON files.

## Architecture

```
┌─────────────────────────────────────────────┐
│                 MCP Tools                    │
│  stub_tools │ persona_tools │ diagnostic    │
├─────────────────────────────────────────────┤
│               Services                       │
│      stub_service │ persona_service          │
├─────────────────────────────────────────────┤
│            Repository                        │
│         stub_repository                      │
├─────────────────────────────────────────────┤
│              Client                          │
│    WireMockHttpClient (httpx)                │
├─────────────────────────────────────────────┤
│         WireMock Admin API                   │
└─────────────────────────────────────────────┘
```

- **Tools layer**: MCP tool definitions, input validation, error wrapping
- **Services layer**: Business logic, persona activation, bulk operations
- **Repository layer**: Data access, WireMock API mapping
- **Client layer**: HTTP transport (httpx), connection management
