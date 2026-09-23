class GatewayError(Exception):
    """Base exception for all Marine Data Gateway errors."""
    pass

class NoProviderAvailableError(GatewayError):
    """Raised when no provider is registered or enabled for a requested capability."""
    def __init__(self, capability: str):
        super().__init__(f"No active provider available for capability: {capability}")

class GatewayTimeoutError(GatewayError):
    """Raised when provider query exceeds maximum allowed gateway timeout."""
    pass

class GatewayRoutingError(GatewayError):
    """Raised when the gateway encounters invalid routing parameters or targets."""
    pass
