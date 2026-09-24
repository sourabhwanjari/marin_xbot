from enum import Enum

class ProviderStatus(str, Enum):
    """
    Standardized operational connectivity status for external marine data providers.
    Phase 5B compliant.
    """
    CONNECTED = "CONNECTED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    DEGRADED = "DEGRADED"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value.upper() == other.upper() or self.name.upper() == other.upper()
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_upper = value.upper()
            for member in cls:
                if member.value == val_upper or member.name == val_upper:
                    return member
        return None
