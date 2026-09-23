class MarineProviderError(Exception):
    """Base exception for all marine data provider failures."""
    pass

class ProviderNotConfiguredError(MarineProviderError):
    """Raised when an external marine data provider is queried but lacks credentials or base configuration."""
    def __init__(self, provider_name: str, missing_config: str):
        self.provider_name = provider_name
        self.missing_config = missing_config
        super().__init__(f"Provider '{provider_name}' is not configured: missing {missing_config}")

class ProviderUnavailableError(MarineProviderError):
    """Raised when an external marine data provider cannot be reached (timeout, connection refused, 5xx)."""
    def __init__(self, provider_name: str, reason: str):
        self.provider_name = provider_name
        self.reason = reason
        super().__init__(f"Provider '{provider_name}' is currently unavailable: {reason}")

class ProviderAuthenticationError(MarineProviderError):
    """Raised when an external marine data provider rejects credentials (401/403)."""
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        super().__init__(f"Authentication failed for provider '{provider_name}'")

class MarineDataFormatError(MarineProviderError):
    """Raised when provider telemetry fails schema validation or normalization."""
    pass
