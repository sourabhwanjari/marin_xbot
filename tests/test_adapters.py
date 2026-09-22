"""
Unit tests for Sonar Data Ingestion & Adapters
"""

import pytest
import os
import tempfile
from pathlib import Path
import numpy as np
import cv2
import json

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from sonar_adapters.image_adapter import ImageAdapter
from sonar_adapters.generic_metadata_adapter import GenericMetadataAdapter
from sonar_adapters.vendor_adapter_stub import FutureVendorAdapterStub


def test_image_adapter_valid():
    adapter = ImageAdapter()
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        temp_path = Path(f.name)

    try:
        # Create 200x200 test image
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        img[50:150, 50:150] = 120
        cv2.imwrite(str(temp_path), img)

        assert adapter.supports(temp_path) is True
        res = adapter.validate(temp_path)
        assert res.is_valid is True
        assert res.status == "GOOD"
        assert res.metadata["width"] == 200
        assert res.metadata["height"] == 200

        data = adapter.read_data(temp_path)
        assert data.shape[:2] == (200, 200)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_image_adapter_corrupt():
    adapter = ImageAdapter()
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(b"NOT_A_VALID_IMAGE_BYTES_123456789")
        temp_path = Path(f.name)

    try:
        res = adapter.validate(temp_path)
        assert res.is_valid is False
        assert res.status == "CRITICAL"
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_generic_metadata_adapter_json():
    adapter = GenericMetadataAdapter()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        payload = [
            {
                "latitude": 18.9220,
                "longitude": 72.8347,
                "heading": 85.0,
                "depth": 28.5,
                "timestamp": "2026-09-14T10:00:00Z"
            }
        ]
        f.write(json.dumps(payload).encode("utf-8"))
        temp_path = Path(f.name)

    try:
        assert adapter.supports(temp_path) is True
        res = adapter.validate(temp_path)
        assert res.is_valid is True
        assert res.metadata["has_gps"] is True
        assert res.metadata["has_timestamp"] is True
        assert res.metadata["has_heading"] is True
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_vendor_adapter_stub_rejection():
    adapter = FutureVendorAdapterStub()
    mock_xtf = Path("survey_swath_01.xtf")
    assert adapter.supports(mock_xtf) is True
    res = adapter.validate(mock_xtf)
    assert res.is_valid is False
    assert res.status == "CRITICAL"
    assert "Proprietary sonar format" in res.messages[0]
