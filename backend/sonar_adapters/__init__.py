"""
SONAR-AI Sonar Ingestion Adapters
Adapter architecture for multi-format sonar files, navigation logs, and vendor streams.
"""

from .base import SonarAdapter, AdapterValidationResult
from .image_adapter import ImageAdapter
from .generic_metadata_adapter import GenericMetadataAdapter
from .vendor_adapter_stub import FutureVendorAdapterStub

__all__ = [
    "SonarAdapter",
    "AdapterValidationResult",
    "ImageAdapter",
    "GenericMetadataAdapter",
    "FutureVendorAdapterStub"
]
