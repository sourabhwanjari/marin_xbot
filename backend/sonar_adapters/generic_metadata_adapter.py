"""
SONAR-AI Generic Metadata Adapter
Parses and validates navigation tracks, GPS telemetry, towfish motion logs from CSV and JSON.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import csv
import io
from datetime import datetime

from .base import SonarAdapter, AdapterValidationResult


class GenericMetadataAdapter(SonarAdapter):
    SUPPORTED_EXTENSIONS = {".csv", ".json", ".txt"}

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def validate(self, file_path: Path) -> AdapterValidationResult:
        messages = []
        if not file_path.exists():
            return AdapterValidationResult(
                is_valid=False,
                status="ERROR",
                messages=["Navigation file does not exist on disk."]
            )

        file_size = file_path.stat().st_size
        if file_size == 0:
            return AdapterValidationResult(
                is_valid=False,
                status="CRITICAL",
                messages=["Navigation file is empty (0 bytes)."]
            )

        records = self.read_data(file_path)
        if not records:
            return AdapterValidationResult(
                is_valid=False,
                status="CRITICAL",
                messages=["No parseable navigation records found in file."]
            )

        messages.append(f"Successfully parsed {len(records)} navigation record(s).")

        # Validate coordinates & fields
        has_gps = False
        has_timestamp = False
        has_heading = False
        has_motion_heave = False
        has_motion_pitch = False
        has_motion_roll = False
        invalid_coords_count = 0
        timestamps = []

        for r in records:
            lat = r.get("latitude") or r.get("lat")
            lon = r.get("longitude") or r.get("lon") or r.get("lng")
            if lat is not None and lon is not None:
                try:
                    lat_f = float(lat)
                    lon_f = float(lon)
                    if -90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0:
                        has_gps = True
                    else:
                        invalid_coords_count += 1
                except (ValueError, TypeError):
                    invalid_coords_count += 1

            ts = r.get("timestamp") or r.get("time") or r.get("date")
            if ts:
                has_timestamp = True
                timestamps.append(str(ts))

            if r.get("heading") is not None or r.get("yaw") is not None:
                has_heading = True
            if r.get("heave") is not None:
                has_motion_heave = True
            if r.get("pitch") is not None:
                has_motion_pitch = True
            if r.get("roll") is not None:
                has_motion_roll = True

        status = "GOOD"

        if not has_gps:
            status = "CRITICAL"
            messages.append("Critical: No valid GPS coordinates (latitude, longitude) detected in file.")
        elif invalid_coords_count > 0:
            status = "WARNING"
            messages.append(f"Warning: {invalid_coords_count} record(s) contained out-of-bounds geographic coordinates.")
        else:
            messages.append("✓ GPS coordinates valid.")

        if has_timestamp:
            messages.append("✓ Timestamps identified.")
        else:
            status = "WARNING"
            messages.append("Warning: Navigation records lack explicit timestamps.")

        # Motion metadata evaluation
        if has_motion_heave:
            messages.append("✓ Heave motion telemetry available.")
        else:
            messages.append("⚠ Notice: Heave data unavailable (motion correction will be partial).")

        if has_motion_pitch:
            messages.append("✓ Pitch telemetry available.")
        else:
            messages.append("⚠ Notice: Pitch data unavailable.")

        if has_motion_roll:
            messages.append("✓ Roll telemetry available.")
        else:
            messages.append("⚠ Notice: Roll data unavailable.")

        return AdapterValidationResult(
            is_valid=has_gps,
            status=status,
            messages=messages,
            metadata={
                "record_count": len(records),
                "has_gps": has_gps,
                "has_timestamp": has_timestamp,
                "has_heading": has_heading,
                "has_heave": has_motion_heave,
                "has_pitch": has_motion_pitch,
                "has_roll": has_motion_roll,
                "motion_availability": "FULL" if (has_motion_heave and has_motion_pitch and has_motion_roll) else ("PARTIAL" if (has_motion_pitch or has_motion_roll or has_motion_heave) else "UNAVAILABLE")
            }
        )

    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        val = self.validate(file_path)
        return val.metadata

    def read_data(self, file_path: Path) -> List[Dict[str, Any]]:
        records = []
        suffix = file_path.suffix.lower()

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                if suffix == ".json":
                    data = json.load(f)
                    if isinstance(data, list):
                        records = data
                    elif isinstance(data, dict):
                        # Could be single record or wrapped
                        if "records" in data and isinstance(data["records"], list):
                            records = data["records"]
                        else:
                            records = [data]
                else:
                    reader = csv.DictReader(f)
                    for row in reader:
                        cleaned = {k.strip(): v.strip() for k, v in row.items() if k}
                        records.append(cleaned)
        except Exception as e:
            print(f"[SONAR-AI] GenericMetadataAdapter read error: {e}")

        return records
