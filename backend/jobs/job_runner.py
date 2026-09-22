"""
SONAR-AI Background Job Runner
Executes multi-stage survey processing jobs asynchronously without blocking HTTP requests.
Maintains state, logs, stage timing, error recovery, and database persistence.
"""

import time
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from pathlib import Path
import cv2

from database import SessionLocal
from models_db import Mission, SurveyFile, ProcessingJob, Detection, ProcessingLog, NavigationPoint
from sonar_adapters.image_adapter import ImageAdapter
from sonar_adapters.generic_metadata_adapter import GenericMetadataAdapter
from sonar_processing.preprocessing import SonarPreprocessor
from sonar_processing.dropout_detection import DropoutDetector
from sonar_processing.motion_compensation import MotionCompensationEngine
from ai.detector import SonarDetector
from ai.model_manager import ModelManager
from ai.postprocessing.filtering import filter_and_postprocess_detections
from geospatial.georeferencing import SonarGeoreferencer


class BackgroundJobManager:
    def __init__(self, max_workers: int = 2):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_jobs: Dict[int, Any] = {}
        self.detector = SonarDetector()

    def start_job(self, job_id: int, mission_id: int, config: Optional[Dict[str, Any]] = None):
        """Dispatches job to thread pool."""
        future = self.executor.submit(self._run_pipeline, job_id, mission_id, config or {})
        self.active_jobs[job_id] = future
        return job_id

    def cancel_job(self, job_id: int) -> bool:
        """Attempts to cancel job."""
        if job_id in self.active_jobs:
            fut = self.active_jobs[job_id]
            cancelled = fut.cancel()
            return cancelled
        return False

    def _log(self, db, mission_id: int, job_id: int, stage: str, level: str, message: str):
        log_entry = ProcessingLog(
            mission_id=mission_id,
            job_id=job_id,
            stage=stage,
            level=level,
            message=message,
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()

    def _update_stage(self, db, job: ProcessingJob, stage_name: str, progress: int, meta: Optional[Dict[str, Any]] = None):
        job.current_stage = stage_name
        job.progress_percent = progress
        current_meta = dict(job.stages_meta or {})
        if meta:
            current_meta[stage_name] = meta
        job.stages_meta = current_meta
        db.commit()

    def _run_pipeline(self, job_id: int, mission_id: int, config: Dict[str, Any]):
        db = SessionLocal()
        start_time = time.time()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        mission = db.query(Mission).filter(Mission.id == mission_id).first()

        if not job or not mission:
            db.close()
            return

        try:
            job.status = "RUNNING"
            mission.status = "PROCESSING"
            db.commit()

            self._log(db, mission_id, job_id, "INIT", "INFO", f"Starting processing pipeline for mission '{mission.name}'.")

            # --- STAGE 1: VALIDATION ---
            t0 = time.time()
            self._update_stage(db, job, "Validation", 10)
            self._log(db, mission_id, job_id, "Validation", "INFO", "Validating survey imagery and navigation files.")

            image_files = db.query(SurveyFile).filter(
                SurveyFile.mission_id == mission_id,
                SurveyFile.file_type == "sonar_image"
            ).all()

            nav_files = db.query(SurveyFile).filter(
                SurveyFile.mission_id == mission_id,
                SurveyFile.file_type.in_(["navigation", "metadata"])
            ).all()

            img_adapter = ImageAdapter()
            meta_adapter = GenericMetadataAdapter()

            validated_images = []
            for f in image_files:
                val = img_adapter.validate(Path(f.file_path))
                f.validation_status = val.status
                f.validation_report = val.to_dict()
                if val.is_valid:
                    f.width = val.metadata.get("width")
                    f.height = val.metadata.get("height")
                    validated_images.append(f)
            db.commit()

            if not validated_images:
                raise ValueError("No valid sonar image files found in mission. Upload JPG, PNG, or TIFF sonar imagery.")

            nav_data = {
                "latitude": 18.9220,
                "longitude": 72.8347,
                "heading": 90.0,
                "depth": 28.5,
                "is_demo_gps": True
            }

            for nf in nav_files:
                val = meta_adapter.validate(Path(nf.file_path))
                nf.validation_status = val.status
                nf.validation_report = val.to_dict()
                if val.is_valid:
                    records = meta_adapter.read_data(Path(nf.file_path))
                    if records:
                        first = records[0]
                        nav_data = {
                            "latitude": float(first.get("latitude") or first.get("lat") or 18.9220),
                            "longitude": float(first.get("longitude") or first.get("lon") or first.get("lng") or 72.8347),
                            "heading": float(first.get("heading") or first.get("yaw") or 90.0),
                            "depth": float(first.get("depth", 28.5)),
                            "heave": float(first["heave"]) if first.get("heave") is not None else None,
                            "pitch": float(first["pitch"]) if first.get("pitch") is not None else None,
                            "roll": float(first["roll"]) if first.get("roll") is not None else None,
                            "is_demo_gps": False
                        }
                        # Save navigation points into DB
                        for r in records:
                            lat = r.get("latitude") or r.get("lat")
                            lon = r.get("longitude") or r.get("lon") or r.get("lng")
                            if lat and lon:
                                try:
                                    np_entry = NavigationPoint(
                                        mission_id=mission_id,
                                        source_file_id=nf.id,
                                        timestamp=str(r.get("timestamp", "")),
                                        ping_id=int(r.get("ping_id", 0)) if r.get("ping_id") else None,
                                        latitude=float(lat),
                                        longitude=float(lon),
                                        heading=float(r.get("heading") or r.get("yaw") or 0.0),
                                        speed=float(r.get("speed", 0.0)) if r.get("speed") else None,
                                        depth=float(r.get("depth", 28.5)) if r.get("depth") else None,
                                        heave=float(r["heave"]) if r.get("heave") is not None else None,
                                        pitch=float(r["pitch"]) if r.get("pitch") is not None else None,
                                        roll=float(r["roll"]) if r.get("roll") is not None else None
                                    )
                                    db.add(np_entry)
                                except (ValueError, TypeError):
                                    pass
            db.commit()
            self._update_stage(db, job, "Validation", 20, {"status": "SUCCESS", "elapsed_s": round(time.time() - t0, 2)})

            # --- STAGE 2: NAVIGATION SYNCHRONIZATION ---
            t0 = time.time()
            self._update_stage(db, job, "Navigation Sync", 30)
            self._log(db, mission_id, job_id, "Navigation Sync", "INFO", f"Synchronized navigation headers (Lat: {nav_data['latitude']:.4f}, Lon: {nav_data['longitude']:.4f}).")
            self._update_stage(db, job, "Navigation Sync", 35, {"status": "SUCCESS", "elapsed_s": round(time.time() - t0, 2)})

            # --- STAGE 3: MOTION CORRECTION EVALUATION ---
            t0 = time.time()
            self._update_stage(db, job, "Motion Correction", 40)
            motion_eng = MotionCompensationEngine()
            motion_eval = motion_eng.evaluate_motion_availability(nav_data)
            self._log(db, mission_id, job_id, "Motion Correction", "INFO" if motion_eval["status"] != "UNAVAILABLE" else "WARNING", motion_eval["summary"])
            self._update_stage(db, job, "Motion Correction", 45, {"status": motion_eval["status"], "elapsed_s": round(time.time() - t0, 2)})

            # --- STAGE 4: DROPOUT DETECTION ---
            t0 = time.time()
            self._update_stage(db, job, "Dropout Detection", 50)
            dropout_det = DropoutDetector()
            first_img_file = validated_images[0]
            raw_img = cv2.imread(first_img_file.file_path, cv2.IMREAD_UNCHANGED)
            dropout_report = dropout_det.detect_image_dropouts(raw_img)
            if dropout_report.get("warning"):
                self._log(db, mission_id, job_id, "Dropout Detection", "WARNING", dropout_report["warning"])
            else:
                self._log(db, mission_id, job_id, "Dropout Detection", "INFO", "No critical acoustic scanline dropouts detected.")
            self._update_stage(db, job, "Dropout Detection", 55, {"status": dropout_report["status"], "elapsed_s": round(time.time() - t0, 2)})

            # --- STAGE 5: SONAR PREPROCESSING ---
            t0 = time.time()
            self._update_stage(db, job, "Sonar Preprocessing", 60)
            enable_denoise = config.get("enable_denoise", True)
            enable_clahe = config.get("enable_clahe", True)
            preprocessor = SonarPreprocessor(
                target_size=1280,
                enable_denoise=enable_denoise,
                enable_clahe=enable_clahe
            )
            processed_img, prep_meta = preprocessor.process(raw_img)
            self._log(db, mission_id, job_id, "Sonar Preprocessing", "INFO", f"Speckle filter & CLAHE applied. Normalized resolution: {prep_meta['processed_width']}x{prep_meta['processed_height']} px.")
            self._update_stage(db, job, "Sonar Preprocessing", 70, {"status": "SUCCESS", "elapsed_s": round(time.time() - t0, 2)})

            # --- STAGE 6: AI INFERENCE ---
            t0 = time.time()
            self._update_stage(db, job, "AI Detection", 75)
            threshold = float(config.get("confidence_threshold", 0.50))
            det_results = self.detector.detect(processed_img, confidence_threshold=threshold)
            raw_candidates = det_results.get("detections", [])
            mode = det_results.get("mode", "demo")
            self._log(db, mission_id, job_id, "AI Detection", "INFO", f"AI inference complete in {mode.upper()} mode. Found {len(raw_candidates)} initial candidate(s).")
            self._update_stage(db, job, "AI Detection", 85, {"status": "SUCCESS", "elapsed_s": round(time.time() - t0, 2)})

            # --- STAGE 7: POSTPROCESSING & FILTERING ---
            t0 = time.time()
            self._update_stage(db, job, "False Positive Filtering", 88)
            filtered_dets = filter_and_postprocess_detections(
                detections=raw_candidates,
                image=processed_img,
                min_confidence=threshold,
                iou_threshold=0.45
            )
            self._log(db, mission_id, job_id, "False Positive Filtering", "INFO", f"After duplicate suppression & acoustic shadow analysis: {len(filtered_dets)} anomaly candidate(s).")
            self._update_stage(db, job, "False Positive Filtering", 90, {"status": "SUCCESS", "elapsed_s": round(time.time() - t0, 2)})

            # --- STAGE 8: GEOREFERENCING ---
            t0 = time.time()
            self._update_stage(db, job, "Georeferencing", 92)
            georeferencer = SonarGeoreferencer(swath_range_m=50.0)
            geotagged_dets = georeferencer.georeference_all(
                detections=filtered_dets,
                nav_data=nav_data,
                img_width=prep_meta["processed_width"],
                img_height=prep_meta["processed_height"]
            )
            self._log(db, mission_id, job_id, "Georeferencing", "INFO", f"Georeferencing complete. Calculated object coordinates and spatial uncertainty radii.")
            self._update_stage(db, job, "Georeferencing", 95, {"status": "SUCCESS", "elapsed_s": round(time.time() - t0, 2)})

            # --- STAGE 9: DETECTION STORAGE ---
            t0 = time.time()
            self._update_stage(db, job, "Detection Storage", 98)

            # Clear old unverified detections for this mission if re-processing
            db.query(Detection).filter(
                Detection.mission_id == mission_id,
                Detection.is_manual == False
            ).delete()

            for d in geotagged_dets:
                det_db = Detection(
                    mission_id=mission_id,
                    source_file_id=first_img_file.id,
                    class_name=d["class"],
                    label=d["label"],
                    ai_confidence=d["confidence"],
                    anomaly_score=d["anomaly_score"],
                    shape_score=d.get("shape_score"),
                    shadow_score=d.get("shadow_score"),
                    bbox_x1=d["bbox"]["x1"],
                    bbox_y1=d["bbox"]["y1"],
                    bbox_x2=d["bbox"]["x2"],
                    bbox_y2=d["bbox"]["y2"],
                    latitude=d.get("latitude"),
                    longitude=d.get("longitude"),
                    depth=d.get("depth"),
                    estimated_width=d.get("estimated_width"),
                    estimated_height=d.get("estimated_height"),
                    location_quality=d.get("location_quality", "APPROXIMATE"),
                    horizontal_uncertainty_m=d.get("horizontal_uncertainty_m"),
                    vertical_uncertainty_m=d.get("vertical_uncertainty_m"),
                    verification_status=d.get("verification_status", "AI_DETECTED"),
                    model_name=d.get("model_name", "sonar_detector"),
                    model_version=d.get("model_version", "1.0"),
                    is_manual=False
                )
                db.add(det_db)
            db.commit()

            # Finalize Job & Mission
            job.status = "COMPLETED"
            job.current_stage = "COMPLETED"
            job.progress_percent = 100
            job.completed_at = datetime.utcnow()
            mission.status = "COMPLETED"
            db.commit()

            total_elapsed = round(time.time() - start_time, 2)
            self._log(db, mission_id, job_id, "FINAL", "SUCCESS", f"Pipeline completed successfully in {total_elapsed}s. {len(geotagged_dets)} anomaly records stored.")

        except Exception as e:
            trace = traceback.format_exc()
            job.status = "FAILED"
            job.error_message = f"{str(e)}"
            job.completed_at = datetime.utcnow()
            mission.status = "FAILED"
            db.commit()
            self._log(db, mission_id, job_id, job.current_stage or "ERROR", "ERROR", f"Job failed: {str(e)}\n{trace}")
        finally:
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            db.close()


_GLOBAL_JOB_MANAGER: Optional[BackgroundJobManager] = None


def get_job_manager() -> BackgroundJobManager:
    global _GLOBAL_JOB_MANAGER
    if _GLOBAL_JOB_MANAGER is None:
        _GLOBAL_JOB_MANAGER = BackgroundJobManager()
    return _GLOBAL_JOB_MANAGER
