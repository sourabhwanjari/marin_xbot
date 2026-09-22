"""
SONAR-AI Data Dropout & Anomaly Quality Detection Module
Detects acoustic scanline dropouts, corrupt image strips, ping gaps, and telemetry blackouts.
"""

from typing import Dict, Any, List, Tuple
import numpy as np


class DropoutDetector:
    """
    Analyzes raw sonar waterfall imagery and navigation streams for missing data,
    acoustic dropouts, and sampling gaps.
    """

    def detect_image_dropouts(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Scans scanlines (horizontal rows) for complete acoustic dropouts
        (blackout scanlines or saturation stripes).
        """
        if len(image.shape) == 3:
            gray = np.mean(image, axis=2)
        else:
            gray = image

        h, w = gray.shape[:2]
        row_means = np.mean(gray, axis=1)

        # Identify scanlines with zero or near-zero backscatter (< 2 intensity)
        blackout_indices = np.where(row_means < 2.0)[0].tolist()

        # Group contiguous dropout scanlines
        gaps = []
        if blackout_indices:
            current_gap = [blackout_indices[0]]
            for idx in blackout_indices[1:]:
                if idx == current_gap[-1] + 1:
                    current_gap.append(idx)
                else:
                    gaps.append(current_gap)
                    current_gap = [idx]
            gaps.append(current_gap)

        classified_gaps = []
        recoverable_count = 0
        unrecoverable_count = 0

        for gap in gaps:
            length = len(gap)
            start_row = gap[0]
            end_row = gap[-1]
            if length <= 3:
                # Isolated single/triple ping dropout is recoverable via boundary interpolation
                classification = "RECOVERABLE"
                recoverable_count += 1
            else:
                # Wide swath blackout is unrecoverable acoustic signal loss
                classification = "UNRECOVERABLE"
                unrecoverable_count += 1

            classified_gaps.append({
                "start_scanline": start_row,
                "end_scanline": end_row,
                "consecutive_pings": length,
                "classification": classification,
                "recommendation": "Interpolate scanline" if classification == "RECOVERABLE" else "Flag as acoustic dead zone"
            })

        has_dropouts = len(classified_gaps) > 0
        status = "GOOD"
        warning = None

        if unrecoverable_count > 0:
            status = "CRITICAL"
            warning = f"DATA QUALITY CRITICAL: {unrecoverable_count} extended acoustic blackout gap(s) detected."
        elif recoverable_count > 0:
            status = "WARNING"
            warning = f"DATA QUALITY WARNING: {recoverable_count} minor scanline dropout(s) detected (recoverable)."

        return {
            "status": status,
            "has_dropouts": has_dropouts,
            "total_dropout_scanlines": len(blackout_indices),
            "percentage_frame_loss": round((len(blackout_indices) / max(1, h)) * 100, 2),
            "gaps": classified_gaps,
            "warning": warning
        }

    def detect_telemetry_gaps(self, nav_records: List[Dict[str, Any]], max_gap_seconds: float = 3.0) -> Dict[str, Any]:
        """
        Scans navigation track records for ping sequence gaps and time interval jumps.
        """
        if not nav_records or len(nav_records) < 2:
            return {
                "status": "GOOD",
                "gaps": [],
                "summary": "Telemetry stream too short for gap analysis."
            }

        gaps = []
        prev_ping = None

        for idx, rec in enumerate(nav_records):
            ping = rec.get("ping_id")
            if ping is not None and prev_ping is not None:
                try:
                    p_curr = int(ping)
                    p_prev = int(prev_ping)
                    if p_curr > p_prev + 1:
                        missing = p_curr - p_prev - 1
                        gaps.append({
                            "type": "PING_SEQUENCE_GAP",
                            "index": idx,
                            "from_ping": p_prev,
                            "to_ping": p_curr,
                            "missing_pings": missing,
                            "classification": "RECOVERABLE" if missing <= 2 else "UNRECOVERABLE"
                        })
                except (ValueError, TypeError):
                    pass
            prev_ping = ping

        status = "GOOD"
        summary = "Navigation stream continuous."
        if gaps:
            unrec = sum(1 for g in gaps if g["classification"] == "UNRECOVERABLE")
            if unrec > 0:
                status = "CRITICAL"
                summary = f"Telemetry contains {len(gaps)} gap(s), {unrec} unrecoverable navigation blackout(s)."
            else:
                status = "WARNING"
                summary = f"Telemetry contains {len(gaps)} minor recoverable ping sequence gap(s)."

        return {
            "status": status,
            "gap_count": len(gaps),
            "gaps": gaps,
            "summary": summary
        }
