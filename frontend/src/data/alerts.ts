import { MarineAlert } from "@/types/marine";

export const mockAlerts: MarineAlert[] = [
  {
    id: "alert-01",
    type: "High Wave Warning",
    severity: "HIGH",
    location: "North Tamil Nadu Coast & Offshore (13.0°N - 13.5°N)",
    latitude: 13.25,
    longitude: 80.60,
    radius_km: 30.0,
    time: "Valid until 18:00 IST Today",
    short_description: "High swell waves of 2.5 - 3.2 meters forecasted along the coast.",
    advisory: "Small mechanized crafts and artisanal boats advised not to venture beyond 15 nautical miles."
  },
  {
    id: "alert-02",
    type: "Lightning Alert",
    severity: "MEDIUM",
    location: "Pulicat Lagoon & Adjacent Waters",
    latitude: 13.45,
    longitude: 80.35,
    radius_km: 15.0,
    time: "Valid for next 4 hours",
    short_description: "Isolated convective thunderstorm activity detected via INSAT-3DR.",
    advisory: "Seek immediate shelter if caught offshore; disconnect tall HF antennas."
  },
  {
    id: "alert-03",
    type: "Strong Wind Advisory",
    severity: "MEDIUM",
    location: "Coromandel Coast Offshore",
    latitude: 12.80,
    longitude: 80.50,
    radius_km: 45.0,
    time: "Continuous Advisory",
    short_description: "Gusty winds reaching 25-30 knots likely during late afternoon squalls.",
    advisory: "Maintain strict engine vigilance; ensure life vests are worn."
  },
  {
    id: "alert-04",
    type: "Restricted Marine Zone",
    severity: "LOW",
    location: "Chennai Port Outer Anchorage & Naval Channel",
    latitude: 13.08,
    longitude: 80.32,
    radius_km: 12.0,
    time: "Permanent Navigation Notice",
    short_description: "Commercial deep-draft vessel fairway and restricted security sector.",
    advisory: "Fishing vessels must not cross security perimeter without Port Control authorization."
  }
];
