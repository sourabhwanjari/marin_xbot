"""
SONAR-AI Detector Module
Executes object detection on Side Scan Sonar imagery.
Uses real YOLO weights if active; otherwise generates deterministic, reproducible
fixtures in DEVELOPMENT MODE with explicit provenance.
"""

from typing import List, Dict, Any, Optional
import hashlib
from datetime import datetime
import numpy as np

from .model_manager import ModelManager


class SonarDetector:
    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.manager = model_manager or ModelManager()

    def get_status(self) -> Dict[str, Any]:
        return self.manager.get_model_status()

    def detect(self, image: np.ndarray, confidence_threshold: float = 0.50) -> Dict[str, Any]:
        """
        Executes inference on preprocessed sonar image numpy array.
        """
        if self.manager.is_real_model and self.manager.model_instance is not None:
            return self._run_real_inference(image, confidence_threshold)
        else:
            return self._run_development_inference(image, confidence_threshold)

    def _run_real_inference(self, image: np.ndarray, confidence_threshold: float) -> Dict[str, Any]:
        results = self.manager.model_instance(image, conf=confidence_threshold)
        detections = []
        det_id = 1

        classes_map = {idx: c for idx, c in enumerate(self.manager.classes)}

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_idx = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                class_info = classes_map.get(cls_idx, {
                    "id": "debris", "label": "Other Debris", "typical_size": (2.0, 1.5)
                })

                pixel_w = abs(x2 - x1)
                pixel_h = abs(y2 - y1)
                est_w = round(float(pixel_w * 0.05), 1)
                est_h = round(float(pixel_h * 0.05), 1)

                detections.append({
                    "id": det_id,
                    "class": class_info["id"],
                    "label": class_info["label"],
                    "confidence": round(conf, 3),
                    "confidence_percent": int(round(conf * 100)),
                    "bbox": {
                        "x1": int(x1),
                        "y1": int(y1),
                        "x2": int(x2),
                        "y2": int(y2)
                    },
                    "estimated_width": max(est_w, 0.5),
                    "estimated_height": max(est_h, 0.5),
                    "model_name": self.manager.model_name,
                    "model_version": self.manager.model_version,
                    "timestamp": datetime.utcnow().isoformat()
                })
                det_id += 1

        return {
            "mode": "model",
            "model_status": self.manager.get_model_status(),
            "detections": detections
        }

    def _run_development_inference(self, image: np.ndarray, confidence_threshold: float) -> Dict[str, Any]:
        """
        Deterministic simulation for development and UI testing.
        Hash-based candidate positioning so results are repeatable for the same image.
        """
        h, w = image.shape[:2]

        # Use image corner samples for hash seed
        sample_bytes = image[::max(1, h // 20), ::max(1, w // 20)].tobytes()
        img_digest = hashlib.md5(sample_bytes).hexdigest()

        candidates = [
            {
                "class_id": "ghost_net", "label": "Ghost Net",
                "rel_x1": 0.18, "rel_y1": 0.22, "rel_w": 0.20, "rel_h": 0.18,
                "confidence": 0.94, "size": (3.4, 2.1)
            },
            {
                "class_id": "shipwreck", "label": "Shipwreck",
                "rel_x1": 0.52, "rel_y1": 0.38, "rel_w": 0.32, "rel_h": 0.24,
                "confidence": 0.88, "size": (11.5, 4.3)
            },
            {
                "class_id": "pipe", "label": "Pipe",
                "rel_x1": 0.25, "rel_y1": 0.68, "rel_w": 0.38, "rel_h": 0.10,
                "confidence": 0.76, "size": (5.8, 0.9)
            },
            {
                "class_id": "cylinder", "label": "Cylinder",
                "rel_x1": 0.74, "rel_y1": 0.16, "rel_w": 0.12, "rel_h": 0.15,
                "confidence": 0.64, "size": (1.9, 0.8)
            },
            {
                "class_id": "debris", "label": "Other Debris",
                "rel_x1": 0.10, "rel_y1": 0.74, "rel_w": 0.10, "rel_h": 0.12,
                "confidence": 0.53, "size": (1.5, 1.2)
            }
        ]

        detections = []
        det_id = 1

        for c in candidates:
            if c["confidence"] < confidence_threshold:
                continue

            x1 = int(c["rel_x1"] * w)
            y1 = int(c["rel_y1"] * h)
            x2 = min(w - 2, x1 + int(c["rel_w"] * w))
            y2 = min(h - 2, y1 + int(c["rel_h"] * h))

            detections.append({
                "id": det_id,
                "class": c["class_id"],
                "label": c["label"],
                "confidence": c["confidence"],
                "confidence_percent": int(round(c["confidence"] * 100)),
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                "estimated_width": c["size"][0],
                "estimated_height": c["size"][1],
                "model_name": "development_simulator",
                "model_version": "0.1.0-dev",
                "timestamp": datetime.utcnow().isoformat()
            })
            det_id += 1

        return {
            "mode": "demo",
            "model_status": self.manager.get_model_status(),
            "detections": detections
        }
