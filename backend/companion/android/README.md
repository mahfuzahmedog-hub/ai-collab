# AIOS Android Companion

Native Android node for the AIOS gateway. Features:
- Talk mode (continuous voice conversation)
- Screen capture → agent context
- Location sharing

## Connection

WebSocket to the gateway (default `127.0.0.1:9100`). Declares capabilities `voice`, `screen`,
`location` on connect. See `app/gateway/protocol.py` for the frame format.

## Status

Placeholder scaffold — implement in a native Android project.
