import { FishingZone } from "@/types/marine";

export const mockFishingZones: FishingZone[] = [
  {
    id: "pfz-01",
    name: "Zone Alpha - Chennai Offshore",
    latitude: 13.12,
    longitude: 80.48,
    distanceKm: 24.0,
    seaSurfaceTemperature: 28.4,
    chlorophyll: "High",
    suitability: "Favorable",
    status: "Favorable",
    dominantSpecies: ["Sardine", "Mackerel", "Tuna"],
    depthMeters: 52
  },
  {
    id: "pfz-02",
    name: "Zone Bravo - Pulicat Shoals",
    latitude: 13.42,
    longitude: 80.42,
    distanceKm: 42.5,
    seaSurfaceTemperature: 28.1,
    chlorophyll: "High",
    suitability: "Favorable",
    status: "Favorable",
    dominantSpecies: ["Anchovy", "Ribbon Fish", "Seer Fish"],
    depthMeters: 38
  },
  {
    id: "pfz-03",
    name: "Zone Charlie - Mahabalipuram Ridge",
    latitude: 12.58,
    longitude: 80.35,
    distanceKm: 35.2,
    seaSurfaceTemperature: 27.9,
    chlorophyll: "Moderate",
    suitability: "Moderate",
    status: "Caution",
    dominantSpecies: ["Squid", "Carangids"],
    depthMeters: 65
  },
  {
    id: "pfz-04",
    name: "Zone Delta - Deep Pelagic Trench",
    latitude: 12.90,
    longitude: 80.85,
    distanceKm: 68.0,
    seaSurfaceTemperature: 29.2,
    chlorophyll: "Low",
    suitability: "Unfavorable",
    status: "Hazard",
    dominantSpecies: ["Yellowfin Tuna"],
    depthMeters: 180
  }
];
