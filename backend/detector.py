"""
Sonar Debris Object Detector Module
Supports real YOLO inference (via Ultralytics) when backend/models/sonar_best.pt exists.
Falls back safely to DEMO MODE with deterministic, realistic debris detection fixtures
when no trained weights are present.
"""

import os
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np

# Class definitions
SONAR_CLASSES = {
    0: {"id": "ghost_net", "label": "Ghost Net", "typical_size": (3.5, 2.2)},
    1: {"id": "shipwreck", "label": "Shipwreck", "typical_size": (12.0, 4.5)},
    2: {"id": "pipe", "label": "Pipe", "typical_size": (6.0, 0.8)},
    3: {"id": "cylinder", "label": "Cylinder", "typical_size": (1.8, 0.9)},
    4: {"id": "debris", "label": "Other Debris", "typical_size": (2.0, 1.5)},
}

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "sonar_best.pt")


class SonarDetector:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.model = None
        self.is_real_model = False
        self._load_model()

    def _load_model(self):
        """Loads YOLO weights if available; otherwise enables DEMO MODE."""
        if os.path.exists(self.model_path):
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.model_path)
                self.is_real_model = True
                print(f"[SONAR-AI] Successfully loaded trained YOLO model from: {self.model_path}")
            except Exception as e:
                print(f"[SONAR-AI] Found {self.model_path} but failed to load: {e}. Defaulting to DEMO MODE.")
                self.model = None
                self.is_real_model = False
        else:
            self.model = None
            self.is_real_model = False
            print(f"[SONAR-AI] No trained model found at '{self.model_path}'. Running in DEMO MODE.")

    def get_status(self) -> Dict[str, Any]:
        """Returns current operational mode."""
        if self.is_real_model:
            return {
                "mode": "model",
                "label": "AI MODEL ACTIVE",
                "description": f"Loaded custom weights from {os.path.basename(self.model_path)}"
            }
        return {
            "mode": "demo",
            "label": "DEMO MODE — No trained sonar model loaded",
            "description": "Simulated detections for interface testing and pipeline demonstration"
        }

    def detect(self, image: np.ndarray, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Executes detection on the given image.
        If real model is active, runs YOLO.
        Otherwise generates deterministic demo detections.
        """
        h, w = image.shape[:2]
        
        if self.is_real_model and self.model is not None:
            return self._run_real_inference(image, confidence_threshold)
        else:
            return self._run_demo_inference(image, confidence_threshold)

    def _run_real_inference(self, image: np.ndarray, confidence_threshold: float) -> Dict[str, Any]:
        """Runs Ultralytics YOLO inference on image numpy array."""
        results = self.model(image, conf=confidence_threshold)
        detections = []
        det_id = 1
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_idx = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                class_info = SONAR_CLASSES.get(cls_idx, {"id": "debris", "label": "Other Debris", "typical_size": (2.0, 1.5)})
                
                # Approximate dimensions based on bounding box aspect ratio
                pixel_w = abs(x2 - x1)
                pixel_h = abs(y2 - y1)
                est_w = round(float(pixel_w * 0.05), 1)  # standard sonar acoustic meter scaling
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
                })
                det_id += 1

        return {
            "mode": "model",
            "model_status": "AI MODEL ACTIVE",
            "detections": detections
        }

    def _run_demo_inference(self, image: np.ndarray, confidence_threshold: float) -> Dict[str, Any]:
        """
        Generates realistic, deterministic demo detections based on image dimensions and content hash.
        Guarantees repeatable, testable results without claiming fake ML precision.
        """
        h, w = image.shape[:2]
        
        # Compute deterministic seed from image shape and summary bytes
        img_digest = hashlib.md5(image[::20, ::20].tobytes()).hexdigest()
        seed = int(img_digest[:8], 16)
        
        # Sample detection layouts positioned safely within image bounds
        demo_candidates = [
            {
                "class_idx": 0,  # Ghost Net
                "rel_x1": 0.18, "rel_y1": 0.22, "rel_w": 0.22, "rel_h": 0.20,
                "confidence": 0.93,
                "est_size": (3.2, 2.1)
            },
            {
                "class_idx": 1,  # Shipwreck
                "rel_x1": 0.52, "rel_y1": 0.38, "rel_w": 0.35, "rel_h": 0.26,
                "confidence": 0.88,
                "est_size": (11.4, 4.2)
            },
            {
                "class_idx": 2,  # Pipe
                "rel_x1": 0.25, "rel_y1": 0.68, "rel_w": 0.40, "rel_h": 0.12,
                "confidence": 0.74,
                "est_size": (5.8, 0.9)
            },
            {
                "class_idx": 3,  # Cylinder
                "rel_x1": 0.75, "rel_y1": 0.15, "rel_w": 0.14, "rel_h": 0.18,
                "confidence": 0.62,
                "est_size": (1.9, 0.8)
            },
            {
                "class_idx": 4,  # Other Debris
                "rel_x1": 0.08, "rel_y1": 0.72, "rel_w": 0.12, "rel_h": 0.14,
                "confidence": 0.54,
                "est_size": (1.6, 1.2)
            }
        ]

        detections = []
        det_id = 1
        
        for cand in demo_candidates:
            conf = cand["confidence"]
            # Filter according to requested threshold
            if conf < confidence_threshold:
                continue
                
            x1 = int(cand["rel_x1"] * w)
            y1 = int(cand["rel_y1"] * h)
            box_w = int(cand["rel_w"] * w)
            box_h = int(cand["rel_h"] * h)
            x2 = min(w - 2, x1 + box_w)
            y2 = min(h - 2, y1 + box_h)
            
            class_info = SONAR_CLASSES[cand["class_idx"]]
            
            detections.append({
                "id": det_id,
                "class": class_info["id"],
                "label": class_info["label"],
                "confidence": conf,
                "confidence_percent": int(round(conf * 100)),
                "bbox": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                },
                "estimated_width": cand["est_size"][0],
                "estimated_height": cand["est_size"][1],
            })
            det_id += 1

        return {
            "mode": "demo",
            "model_status": "DEMO MODE — No trained sonar model loaded",
            "detections": detections
        }
