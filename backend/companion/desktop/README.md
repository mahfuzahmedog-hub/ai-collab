# AIOS Desktop Companion

Electron/Nextron desktop app that pairs with the AIOS gateway. Features:
- System tray + push-to-talk
- Local MCP mode (host tools on the desktop)
- Canvas surface for agent output

## Connection

WebSocket to the gateway (default `127.0.0.1:9100`). Declares capability `canvas` and can host
local MCP servers discovered via `app.mcp.registry`.

## Status

Placeholder scaffold — build the Electron shell and wire the WebSocket client.
