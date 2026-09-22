"""
SONAR-AI Database Models
Defines relational schemas for missions, survey files, navigation telemetry,
background processing jobs, AI detections, and human verification audit trails.
"""

from datetime import datetime
import json
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from database import Base


class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    survey_date = Column(String(50), nullable=True)
    operator = Column(String(255), nullable=True)
    vessel_auv = Column(String(255), nullable=True)
    sonar_device = Column(String(255), nullable=True)
    survey_area = Column(String(255), nullable=True)
    crs = Column(String(50), default="EPSG:4326 (WGS84)")
    status = Column(String(50), default="READY")  # READY, PROCESSING, COMPLETED, ARCHIVED, ERROR
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    files = relationship("SurveyFile", back_populates="mission", cascade="all, delete-orphan")
    jobs = relationship("ProcessingJob", back_populates="mission", cascade="all, delete-orphan")
    navigation_points = relationship("NavigationPoint", back_populates="mission", cascade="all, delete-orphan")
    detections = relationship("Detection", back_populates="mission", cascade="all, delete-orphan")
    logs = relationship("ProcessingLog", back_populates="mission", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "survey_date": self.survey_date,
            "operator": self.operator,
            "vessel_auv": self.vessel_auv,
            "sonar_device": self.sonar_device,
            "survey_area": self.survey_area,
            "crs": self.crs,
            "status": self.status,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "file_count": len(self.files) if self.files else 0,
            "detection_count": len(self.detections) if self.detections else 0
        }


class SurveyFile(Base):
    __tablename__ = "survey_files"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # sonar_image, navigation, metadata
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), nullable=True)
    validation_status = Column(String(50), default="UNVALIDATED")  # GOOD, WARNING, CRITICAL, ERROR
    validation_report = Column(JSON, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    mission = relationship("Mission", back_populates="files")
    detections = relationship("Detection", back_populates="source_file")

    def to_dict(self):
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "validation_status": self.validation_status,
            "validation_report": self.validation_report or {},
            "width": self.width,
            "height": self.height,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    current_stage = Column(String(100), default="INIT")
    progress_percent = Column(Integer, default=0)
    stages_meta = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    config = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    mission = relationship("Mission", back_populates="jobs")
    logs = relationship("ProcessingLog", back_populates="job", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "status": self.status,
            "current_stage": self.current_stage,
            "progress_percent": self.progress_percent,
            "stages_meta": self.stages_meta or {},
            "error_message": self.error_message,
            "config": self.config or {},
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class NavigationPoint(Base):
    __tablename__ = "navigation_points"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    source_file_id = Column(Integer, ForeignKey("survey_files.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(String(50), nullable=True)
    ping_id = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    heading = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    depth = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    range = Column(Float, nullable=True)
    heave = Column(Float, nullable=True)
    pitch = Column(Float, nullable=True)
    roll = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    mission = relationship("Mission", back_populates="navigation_points")

    def to_dict(self):
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "timestamp": self.timestamp,
            "ping_id": self.ping_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "heading": self.heading,
            "speed": self.speed,
            "depth": self.depth,
            "altitude": self.altitude,
            "range": self.range,
            "heave": self.heave,
            "pitch": self.pitch,
            "roll": self.roll
        }


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    source_file_id = Column(Integer, ForeignKey("survey_files.id", ondelete="SET NULL"), nullable=True)

    # Class & Labels
    class_name = Column(String(100), nullable=False)  # ghost_net, shipwreck, pipe, cylinder, debris
    label = Column(String(100), nullable=False)

    # Scoring
    ai_confidence = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    shape_score = Column(Float, nullable=True)
    shadow_score = Column(Float, nullable=True)

    # Bounding Box (pixel coordinates)
    bbox_x1 = Column(Integer, nullable=False)
    bbox_y1 = Column(Integer, nullable=False)
    bbox_x2 = Column(Integer, nullable=False)
    bbox_y2 = Column(Integer, nullable=False)

    # Physical Dimensions & Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    depth = Column(Float, nullable=True)
    estimated_width = Column(Float, nullable=True)
    estimated_height = Column(Float, nullable=True)
    location_quality = Column(String(50), default="APPROXIMATE")  # EXACT / HIGH QUALITY, ESTIMATED, APPROXIMATE, UNAVAILABLE
    horizontal_uncertainty_m = Column(Float, nullable=True)
    vertical_uncertainty_m = Column(Float, nullable=True)

    # Status: AI_DETECTED, NEEDS_REVIEW, VERIFIED, REJECTED, MODIFIED
    verification_status = Column(String(50), default="AI_DETECTED", index=True)

    # Provenance
    model_name = Column(String(100), default="sonar_detector")
    model_version = Column(String(50), default="1.0")
    is_manual = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    mission = relationship("Mission", back_populates="detections")
    source_file = relationship("SurveyFile", back_populates="detections")
    reviews = relationship("DetectionReview", back_populates="detection", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "source_file_id": self.source_file_id,
            "class_name": self.class_name,
            "label": self.label,
            "ai_confidence": round(float(self.ai_confidence), 3),
            "ai_confidence_percent": int(round(self.ai_confidence * 100)),
            "anomaly_score": round(float(self.anomaly_score), 3),
            "anomaly_score_percent": int(round(self.anomaly_score * 100)),
            "shape_score": round(float(self.shape_score), 3) if self.shape_score is not None else None,
            "shadow_score": round(float(self.shadow_score), 3) if self.shadow_score is not None else None,
            "bbox": {
                "x1": self.bbox_x1,
                "y1": self.bbox_y1,
                "x2": self.bbox_x2,
                "y2": self.bbox_y2
            },
            "latitude": self.latitude,
            "longitude": self.longitude,
            "depth": self.depth,
            "estimated_width": self.estimated_width,
            "estimated_height": self.estimated_height,
            "location_quality": self.location_quality,
            "horizontal_uncertainty_m": self.horizontal_uncertainty_m,
            "vertical_uncertainty_m": self.vertical_uncertainty_m,
            "verification_status": self.verification_status,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "is_manual": self.is_manual,
            "review_count": len(self.reviews) if self.reviews else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class DetectionReview(Base):
    __tablename__ = "detection_reviews"

    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id", ondelete="CASCADE"), nullable=False)
    engineer = Column(String(255), default="Sonar Review Engineer")
    action = Column(String(50), nullable=False)  # CONFIRM, REJECT, MODIFY, RECLASSIFY, MANUAL_ADD
    original_class = Column(String(100), nullable=True)
    new_class = Column(String(100), nullable=True)
    original_bbox = Column(JSON, nullable=True)
    new_bbox = Column(JSON, nullable=True)
    original_confidence = Column(Float, nullable=True)
    comments = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    detection = relationship("Detection", back_populates="reviews")

    def to_dict(self):
        return {
            "id": self.id,
            "detection_id": self.detection_id,
            "engineer": self.engineer,
            "action": self.action,
            "original_class": self.original_class,
            "new_class": self.new_class,
            "original_bbox": self.original_bbox,
            "new_bbox": self.new_bbox,
            "original_confidence": self.original_confidence,
            "comments": self.comments,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class ProcessingLog(Base):
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=True)
    stage = Column(String(100), nullable=False)
    level = Column(String(20), default="INFO")  # INFO, WARNING, ERROR, SUCCESS
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    mission = relationship("Mission", back_populates="logs")
    job = relationship("ProcessingJob", back_populates="logs")

    def to_dict(self):
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "job_id": self.job_id,
            "stage": self.stage,
            "level": self.level,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
