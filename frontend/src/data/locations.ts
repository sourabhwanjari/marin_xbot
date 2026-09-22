import { UserLocation, HazardArea, RestrictedArea } from "@/types/marine";

export const defaultUserLocation: UserLocation = {
  name: "Chennai Fishing Harbour (Kasimedu)",
  latitude: 13.125,
  longitude: 80.298,
  portName: "Chennai Major Port & Artisanal Wharf"
};

export const mockHazardAreas: HazardArea[] = [
  {
    id: "hazard-area-01",
    name: "Northern Swell Risk Polygon",
    type: "High Wave",
    severity: "HIGH",
    coordinates: [
      [13.15, 80.50],
      [13.35, 80.70],
      [13.20, 80.85],
      [13.05, 80.60]
    ],
    description: "Concentrated 3.2m sea swell corridor driven by offshore wind fetch."
  }
];

export const mockRestrictedAreas: RestrictedArea[] = [
  {
    id: "restricted-area-01",
    name: "Port Outer Anchorage Fairway",
    type: "Port Security",
    coordinates: [
      [13.06, 80.31],
      [13.10, 80.35],
      [13.08, 80.38],
      [13.04, 80.33]
    ],
    description: "Designated deep-draft tanker navigation corridor. Artisanal fishing strictly prohibited."
  },
  {
    id: "restricted-area-02",
    name: "Pulicat Marine Conservation Zone",
    type: "Marine Sanctuary",
    coordinates: [
      [13.40, 80.28],
      [13.48, 80.32],
      [13.45, 80.38],
      [13.38, 80.34]
    ],
    description: "Estuarine nursery habitat; mechanized bottom-trawling barred under coastal conservation law."
  }
];
