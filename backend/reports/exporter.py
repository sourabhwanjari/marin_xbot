"""
SONAR-AI Report Exporter
Generates CSV, JSON, GeoJSON, and PDF survey anomaly reports.
"""

import os
import csv
import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from config import REPORTS_DIR
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class SurveyReportExporter:
    def __init__(self, output_dir: Path = REPORTS_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_csv(self, mission_data: Dict[str, Any], detections: List[Dict[str, Any]], filename: str) -> Path:
        file_path = self.output_dir / filename
        fieldnames = [
            "ID", "Classification", "AI Confidence", "Anomaly Score", "Verification Status",
            "Latitude", "Longitude", "Depth (m)", "Est Width (m)", "Est Height (m)",
            "Location Quality", "Horizontal Uncertainty (m)", "Model Version", "Timestamp"
        ]

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(fieldnames)
            for d in detections:
                conf_pct = d.get('ai_confidence_percent') or d.get('confidence_percent') or int(round(float(d.get('ai_confidence') or d.get('confidence') or 0) * 100))
                anom_pct = d.get('anomaly_score_percent') or int(round(float(d.get('anomaly_score') or 0) * 100))
                writer.writerow([
                    d.get("id"),
                    d.get("label", d.get("class_name")),
                    f"{conf_pct}%",
                    f"{anom_pct}%",
                    d.get("verification_status", "AI_DETECTED"),
                    d.get("latitude", ""),
                    d.get("longitude", ""),
                    d.get("depth", ""),
                    d.get("estimated_width", ""),
                    d.get("estimated_height", ""),
                    d.get("location_quality", ""),
                    d.get("horizontal_uncertainty_m", ""),
                    d.get("model_version", ""),
                    d.get("created_at", "")
                ])
        return file_path

    def export_json(self, mission_data: Dict[str, Any], detections: List[Dict[str, Any]], filename: str) -> Path:
        file_path = self.output_dir / filename
        total = len(detections)
        verified = sum(1 for d in detections if d.get("verification_status") == "VERIFIED")
        rejected = sum(1 for d in detections if d.get("verification_status") == "REJECTED")
        needs_review = sum(1 for d in detections if d.get("verification_status") in ["NEEDS_REVIEW", "AI_DETECTED"])

        payload = {
            "system": "SONAR-AI Marine Survey & Underwater Anomaly Detection System",
            "generated_at": datetime.utcnow().isoformat(),
            "mission": mission_data,
            "summary": {
                "total_anomalies": total,
                "verified": verified,
                "rejected": rejected,
                "needs_review": needs_review
            },
            "detections": detections,
            "disclaimer": (
                "Side Scan Sonar interpretation depends strongly on sonar frequency, range, vehicle motion, "
                "seafloor conditions, object orientation, acoustic shadows, and training-data quality. "
                "AI detections require human engineer verification before being considered confirmed survey findings."
            )
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return file_path

    def export_geojson(self, mission_data: Dict[str, Any], detections: List[Dict[str, Any]], filename: str) -> Path:
        file_path = self.output_dir / filename
        features = []

        for d in detections:
            lat = d.get("latitude")
            lon = d.get("longitude")
            if lat is not None and lon is not None:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(lon), float(lat)]
                    },
                    "properties": {
                        "id": d.get("id"),
                        "class_name": d.get("class_name"),
                        "label": d.get("label"),
                        "ai_confidence": d.get("ai_confidence"),
                        "anomaly_score": d.get("anomaly_score"),
                        "verification_status": d.get("verification_status"),
                        "depth_m": d.get("depth"),
                        "location_quality": d.get("location_quality"),
                        "horizontal_uncertainty_m": d.get("horizontal_uncertainty_m"),
                        "mission_id": mission_data.get("id"),
                        "mission_name": mission_data.get("name")
                    }
                })

        geojson = {
            "type": "FeatureCollection",
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
            },
            "features": features
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2)
        return file_path

    def export_pdf(self, mission_data: Dict[str, Any], detections: List[Dict[str, Any]], filename: str) -> Path:
        file_path = self.output_dir / filename
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a")
        )
        heading_style = ParagraphStyle(
            'H2Style',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155")
        )
        badge_style = ParagraphStyle(
            'BadgeStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#0284c7")
        )

        story = []

        # Title and Header
        story.append(Paragraph("SONAR-AI — MARINE SURVEY ANOMALY REPORT", title_style))
        story.append(Paragraph(f"Autonomous Underwater Survey Anomaly Inspection & Verification Dossier", badge_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceBefore=2, spaceAfter=8))

        # Mission Overview Table
        mission_info = [
            [Paragraph("<b>Mission Name:</b>", body_style), Paragraph(str(mission_data.get("name", "N/A")), body_style),
             Paragraph("<b>Date:</b>", body_style), Paragraph(str(mission_data.get("survey_date", datetime.utcnow().strftime("%Y-%m-%d"))), body_style)],
            [Paragraph("<b>Survey Area:</b>", body_style), Paragraph(str(mission_data.get("survey_area", "N/A")), body_style),
             Paragraph("<b>Operator:</b>", body_style), Paragraph(str(mission_data.get("operator", "Sonar Hydrographer")), body_style)],
            [Paragraph("<b>Vessel / AUV:</b>", body_style), Paragraph(str(mission_data.get("vessel_auv", "Survey Vessel")), body_style),
             Paragraph("<b>Sonar Device:</b>", body_style), Paragraph(str(mission_data.get("sonar_device", "Dual Frequency SSS")), body_style)],
            [Paragraph("<b>Coordinate System:</b>", body_style), Paragraph(str(mission_data.get("crs", "EPSG:4326 (WGS84)")), body_style),
             Paragraph("<b>Report Generated:</b>", body_style), Paragraph(datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), body_style)]
        ]

        t_mission = Table(mission_info, colWidths=[100, 170, 100, 170])
        t_mission.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_mission)
        story.append(Spacer(1, 12))

        # Survey Statistics Summary Box
        total = len(detections)
        verified = sum(1 for d in detections if d.get("verification_status") == "VERIFIED")
        rejected = sum(1 for d in detections if d.get("verification_status") == "REJECTED")
        needs_rev = sum(1 for d in detections if d.get("verification_status") in ["NEEDS_REVIEW", "AI_DETECTED"])

        stat_data = [
            [
                Paragraph("<b>Total Targets Analyzed</b>", body_style),
                Paragraph("<b>Verified Anomalies</b>", body_style),
                Paragraph("<b>Needs Review</b>", body_style),
                Paragraph("<b>Rejected (Natural/Noise)</b>", body_style)
            ],
            [
                Paragraph(f"<font size=14 color='#0284c7'><b>{total}</b></font>", body_style),
                Paragraph(f"<font size=14 color='#16a34a'><b>{verified}</b></font>", body_style),
                Paragraph(f"<font size=14 color='#ca8a04'><b>{needs_rev}</b></font>", body_style),
                Paragraph(f"<font size=14 color='#dc2626'><b>{rejected}</b></font>", body_style)
            ]
        ]
        t_stats = Table(stat_data, colWidths=[135, 135, 135, 135])
        t_stats.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_stats)
        story.append(Spacer(1, 14))

        # Detected Anomalies Table
        story.append(Paragraph("Survey Target Detections & Verification Breakdown", heading_style))
        story.append(Spacer(1, 4))

        table_rows = [
            ["ID", "Object Type", "AI Conf", "Anomaly", "Verification", "Latitude", "Longitude", "Depth", "Quality"]
        ]

        for d in detections[:40]:  # Cap at 40 rows per table for clean PDF presentation
            status_text = d.get("verification_status", "AI_DETECTED")
            table_rows.append([
                str(d.get("id")),
                str(d.get("label", d.get("class_name"))),
                f"{d.get('ai_confidence_percent', int(d.get('ai_confidence', 0) * 100))}%",
                f"{d.get('anomaly_score_percent', int(d.get('anomaly_score', 0) * 100))}%",
                status_text,
                f"{d.get('latitude', 0):.5f}" if d.get("latitude") else "N/A",
                f"{d.get('longitude', 0):.5f}" if d.get("longitude") else "N/A",
                f"{d.get('depth', 0):.1f}m" if d.get("depth") else "-",
                str(d.get("location_quality", "APPROX"))[:8]
            ])

        col_widths = [25, 80, 50, 50, 75, 70, 70, 45, 75]
        t_dets = Table(table_rows, colWidths=col_widths, repeatRows=1)
        t_dets.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('TOPPADDING', (0, 0), (-1, 0), 5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")])
        ]))
        story.append(t_dets)
        story.append(Spacer(1, 14))

        # Scientific Limitations & Sign-off
        story.append(Paragraph("<b>SURVEY QUALITY & SCIENTIFIC LIMITATIONS:</b>", ParagraphStyle('LimHead', parent=body_style, fontName='Helvetica-Bold', fontSize=8)))
        limitation_text = (
            "Side Scan Sonar interpretation depends upon frequency, range, towfish motion, grazing angle, "
            "seafloor sediment backscatter, and training data representation. "
            "AI detections serve as engineering decision-support alerts and must be confirmed by an offshore hydrographer "
            "before physical intervention or salvage."
        )
        story.append(Paragraph(limitation_text, ParagraphStyle('LimText', parent=body_style, fontSize=7.5, textColor=colors.HexColor("#64748b"))))
        story.append(Spacer(1, 10))

        # Signature line
        sig_data = [
            [Paragraph("<b>Lead Hydrographer / Reviewer:</b> ___________________________", body_style),
             Paragraph("<b>Verification Signature:</b> ___________________________", body_style)]
        ]
        t_sig = Table(sig_data, colWidths=[270, 270])
        story.append(t_sig)

        doc.build(story)
        return file_path
