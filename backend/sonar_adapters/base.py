"""
SONAR-AI Base Sonar Adapter
Defines the abstract interface for all sonar data adapters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path


@dataclass
class AdapterValidationResult:
    is_valid: bool
    status: str  # GOOD, WARNING, CRITICAL, ERROR
    messages: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "status": self.status,
            "messages": self.messages,
            "metadata": self.metadata
        }


class SonarAdapter(ABC):
    """
    Abstract interface for parsing and validating side scan sonar imagery,
    navigation tracks, and proprietary acoustic telemetry.
    """

    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """Determines whether this adapter can parse the given file."""
        pass

    @abstractmethod
    def validate(self, file_path: Path) -> AdapterValidationResult:
        """
        Validates file integrity, format compliance, coordinate sanity,
        and data completeness. Returns structured status.
        """
        pass

    @abstractmethod
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extracts native physical dimensions, timestamps, GPS headers, and sensor metadata."""
        pass

    @abstractmethod
    def read_data(self, file_path: Path) -> Any:
        """Loads data into memory as a standard representation (numpy array or records)."""
        pass
