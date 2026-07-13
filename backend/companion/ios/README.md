# AIOS iOS Companion

A native iOS companion node for the AIOS gateway. It connects over WebSocket, exposes:
- Voice trigger (wake word detection)
- Camera capture → LLM vision
- Canvas surface for agent output

## Connection

Point it at the AIOS gateway host/port (default `127.0.0.1:9100`). On first connect the node
registers a device identity and declares capabilities (`voice`, `camera`, `canvas`).

## Status

Placeholder scaffold — wire UI + WebSocket client in a native iOS project. The gateway protocol
in `app/gateway/protocol.py` defines the frame format (JSON-RPC over WebSocket).
