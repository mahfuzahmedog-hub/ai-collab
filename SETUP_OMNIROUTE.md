# OmniRoute LLM Integration Setup

OmniRoute is an LLM gateway that routes requests to multiple model providers through a single OpenAI-compatible API. This setup replaces the simulated agent responses in the AIOS platform with real LLM calls.

## What Changed

1. **`src/convex/llm.ts`** — Added `omniroute` provider with support for `OMNIROUTE_API_KEY`, `OMNIROUTE_BASE_URL`, `OMNIROUTE_DEFAULT_MODEL` environment variables.
2. **`src/convex/agentOrchestration.ts`** — Now uses real LLM responses when `OMNIROUTE_API_KEY` is set, falling back to simulated responses otherwise.
3. **`.env`** / **`.env.example`** — Added OmniRoute configuration variables.

## Setup Steps

### 1. Get an OmniRoute API Key

- **Local**: Run OmniRoute locally (default `http://localhost:20128/v1`, key `sk_omniroute`)
- **Hosted**: Get your API key from [omniroute.ai](https://omniroute.ai)

### 2. Configure Convex Environment Variables

The Convex backend needs the API key set in its deployment environment:

```bash
npx convex env set OMNIROUTE_API_KEY "your-api-key-here"
npx convex env set OMNIROUTE_BASE_URL "http://localhost:20128/v1"
npx convex env set OMNIROUTE_DEFAULT_MODEL "auto"
```

### 3. Deploy Convex Functions

```bash
npx convex dev
```

### 4. Run the Frontend

```bash
npm run dev
```

## How It Works

When `OMNIROUTE_API_KEY` is present in the Convex environment:

1. User sends a message → `processUserMessage` action runs
2. For each responding agent (Boss + relevant specialists):
   - Fetches conversation history
   - Calls `generateAgentResponse` with `provider: "omniroute"`
   - `llm.ts` sends request to OmniRoute's OpenAI-compatible endpoint
   - Response is posted to the chat channel
3. Each agent's system prompt + capabilities are passed as context

When `OMNIROUTE_API_KEY` is NOT set, the platform falls back to keyword-based simulated responses (no API key required for demo).

## Provider Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OMNIROUTE_API_KEY` | `sk_omniroute` | API key for OmniRoute gateway |
| `OMNIROUTE_BASE_URL` | `http://localhost:20128/v1` | OmniRoute endpoint |
| `OMNIROUTE_DEFAULT_MODEL` | `auto` | Default model (auto-routes to best available) |

## Adding OmniRoute Models

OmniRoute supports multiple models via prefixes (see `opencode.json` for the full list):
- `auto/coding`, `auto/fast`, `auto/smart`, `auto/reasoning`, `auto/vision`
- `ddgw/gpt-4o-mini`, `ddgw/claude-3-5-haiku-20241022`
- `aug/gpt-5.5-high`, `aug/claude-sonnet-4.6`
- `oc/big-pickle`, and many more

Set the model per-agent via the `llmModel` field in `agents.ts`.

## Backend (Python/FastAPI) Integration

The Python backend already supports OmniRoute. To enable:

```bash
# backend/.env
OMNIROUTE_API_KEY=your-key
OMNIROUTE_BASE_URL=http://localhost:20128/v1
OMNIROUTE_DEFAULT_MODEL=auto
LLM_DEFAULT_PROVIDER=omniroute
```
