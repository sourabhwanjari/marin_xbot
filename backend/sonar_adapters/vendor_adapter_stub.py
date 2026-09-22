"""
SONAR-AI Future Vendor Adapter Stub
Template and interface contract for proprietary acoustic formats
such as eXtended Triton Format (.xtf), EdgeTech (.jsf), and Kongsberg (.all/.kmall).

SCIENTIFIC INTEGRITY NOTE:
This system does NOT pretend to decode proprietary binary packets without a validated
specification parser. When encountered, this adapter identifies the file signature
and provides structured guidance rather than pretending to parse unsupported binary streams.
"""

from pathlib import Path
from typing import Dict, Any
from .base import SonarAdapter, AdapterValidationResult


class FutureVendorAdapterStub(SonarAdapter):
    PROPRIETARY_EXTENSIONS = {".xtf", ".jsf", ".all", ".kmall", ".sgy", ".segy"}

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.PROPRIETARY_EXTENSIONS

    def validate(self, file_path: Path) -> AdapterValidationResult:
        ext = file_path.suffix.lower()
        return AdapterValidationResult(
            is_valid=False,
            status="CRITICAL",
            messages=[
                f"Proprietary sonar format '{ext}' detected ({file_path.name}).",
                f"SONAR-AI does not pretend to decode unverified binary packages.",
                f"Please export this survey swath to georeferenced TIFF, PNG, or CSV telemetry using vendor hydrographic software (e.g. SonarWiz, CARIS, EdgeTech Discover) before ingesting."
            ],
            metadata={
                "extension": ext,
                "vendor_support_status": "PLANNED_PHASE_2"
            }
        )

    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        return {"error": "Proprietary format not decoded in this version."}

    def read_data(self, file_path: Path) -> Any:
        raise NotImplementedError(
            f"Proprietary parser for '{file_path.suffix}' is planned for future vendor releases. "
            "Convert to GeoTIFF / CSV for immediate analysis."
        )
