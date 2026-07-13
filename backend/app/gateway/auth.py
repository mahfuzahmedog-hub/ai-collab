from __future__ import annotations
import hashlib
import hmac
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class AuthMode(Enum):
    shared_secret = "shared_secret"
    tailscale = "tailscale"
    trusted_proxy = "trusted_proxy"
    none = "none"


class GatewayAuth:
    def __init__(self, mode: AuthMode = AuthMode.none, shared_secret: str = ""):
        self.mode = mode
        self.shared_secret = shared_secret

    async def authenticate(self, token: str, peer_addr: str = "") -> bool:
        if self.mode == AuthMode.none:
            return True
        if self.mode == AuthMode.shared_secret:
            return self._verify_shared_secret(token)
        if self.mode == AuthMode.trusted_proxy:
            return True
        return False

    def _verify_shared_secret(self, token: str) -> bool:
        if not self.shared_secret or not token:
            return False
        expected = hmac.new(
            self.shared_secret.encode(), b"gateway-auth", hashlib.sha256
        ).hexdigest()[:16]
        return hmac.compare_digest(token, expected)

    def generate_token(self) -> str:
        return hmac.new(
            self.shared_secret.encode(), b"gateway-auth", hashlib.sha256
        ).hexdigest()[:16]
