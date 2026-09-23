"use client";

import React, { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";
import { FishingZone, MarineAlert, UserLocation, HazardArea, RestrictedArea } from "@/types/marine";
import MapLegend from "./MapLegend";

interface MarineMapProps {
  userLocation: UserLocation;
  fishingZones: FishingZone[];
  alerts: MarineAlert[];
  hazardAreas: HazardArea[];
  restrictedAreas: RestrictedArea[];
  selectedZoneId?: string | null;
  onZoneSelect?: (zone: FishingZone) => void;
}

export const MarineMap: React.FC<MarineMapProps> = ({
  userLocation,
  fishingZones,
  alerts,
  hazardAreas,
  restrictedAreas,
  selectedZoneId,
  onZoneSelect,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const layersRef = useRef<any[]>([]);

  useEffect(() => {
    let isMounted = true;

    async function initMap() {
      if (!mapContainerRef.current || mapInstanceRef.current) return;

      const L = (await import("leaflet")).default;

      // Create map instance centered on user location
      const map = L.map(mapContainerRef.current, {
        center: [userLocation.latitude, userLocation.longitude + 0.15],
        zoom: 10,
        minZoom: 6,
        maxZoom: 16,
        zoomControl: false,
      });

      // Position zoom controls in top-left
      L.control.zoom({ position: "topleft" }).addTo(map);

      // CartoDB Voyager tiles (crisp and bright for professional white theme)
      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        {
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
          subdomains: "abcd",
          maxZoom: 19,
        }
      ).addTo(map);

      mapInstanceRef.current = map;

      // Draw all layers
      renderLayers(L, map);
    }

    initMap();

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  const [layersEnabled, setLayersEnabled] = React.useState({
    pfz: true,
    restricted: true,
    hazards: true,
    alerts: true,
  });

  // Update layers when props or layer toggles change
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    import("leaflet").then((L) => {
      renderLayers(L.default, mapInstanceRef.current);
    });
  }, [fishingZones, alerts, hazardAreas, restrictedAreas, selectedZoneId, layersEnabled]);

  const renderLayers = (L: any, map: any) => {
    // Clear previous layers
    layersRef.current.forEach((layer) => layer.remove());
    layersRef.current = [];

    // 1. User Location Marker (Blue)
    const userMarker = L.circleMarker([userLocation.latitude, userLocation.longitude], {
      radius: 9,
      fillColor: "#2563EB",
      color: "#FFFFFF",
      weight: 2,
      opacity: 1,
      fillOpacity: 0.95,
    }).addTo(map);

    // User ping radius
    const userAccuracy = L.circle([userLocation.latitude, userLocation.longitude], {
      radius: 2500,
      fillColor: "#3B82F6",
      color: "#2563EB",
      weight: 1.5,
      opacity: 0.5,
      fillOpacity: 0.08,
      dashArray: "4, 6",
    }).addTo(map);

    userMarker.bindPopup(`
      <div style="font-family: sans-serif; color: #0f172a; min-width: 180px;">
        <div style="font-weight: 700; font-size: 13px; color: #2563eb; margin-bottom: 4px;">🔵 User Position</div>
        <div style="font-size: 12px; font-weight: 600;">${userLocation.name}</div>
        <div style="font-size: 11px; color: #64748b; margin-top: 2px;">${userLocation.portName}</div>
        <div style="font-size: 11px; margin-top: 4px; font-family: monospace;">Lat: ${userLocation.latitude.toFixed(3)}°, Lon: ${userLocation.longitude.toFixed(3)}°</div>
      </div>
    `);

    layersRef.current.push(userMarker, userAccuracy);

    // 2. Potential Fishing Zones (PFZs)
    if (layersEnabled.pfz) {
      fishingZones.forEach((zone) => {
        let fillColor = "#10B981"; // Emerald / Green
        let strokeColor = "#059669";
        let statusLabel = "🟢 Favorable PFZ";

        if (zone.status === "Caution") {
          fillColor = "#F59E0B";
          strokeColor = "#D97706";
          statusLabel = "🟡 Caution Area";
        } else if (zone.status === "Hazard") {
          fillColor = "#EF4444";
          strokeColor = "#DC2626";
          statusLabel = "🔴 Unfavorable / High Risk";
        }

        // Main Marker
        const pfzMarker = L.circleMarker([zone.latitude, zone.longitude], {
          radius: 11,
          fillColor: fillColor,
          color: "#FFFFFF",
          weight: 2,
          opacity: 1,
          fillOpacity: 0.9,
        }).addTo(map);

        // Zone Coverage Circle
        const pfzRadius = L.circle([zone.latitude, zone.longitude], {
          radius: 3500,
          fillColor: fillColor,
          color: strokeColor,
          weight: 1.5,
          opacity: 0.6,
          fillOpacity: 0.15,
        }).addTo(map);

        pfzMarker.bindPopup(`
          <div style="font-family: sans-serif; color: #0f172a; min-width: 220px;">
            <div style="font-weight: 700; font-size: 13px; color: ${strokeColor}; margin-bottom: 4px;">
              ${statusLabel}
            </div>
            <div style="font-size: 13px; font-weight: 600; margin-bottom: 4px;">${zone.name}</div>
            <div style="font-size: 11px; color: #475569; line-height: 1.4;">
              <div>• <b>Distance:</b> ${zone.distanceKm} km from port</div>
              <div>• <b>SST:</b> ${zone.seaSurfaceTemperature}°C</div>
              <div>• <b>Chlorophyll:</b> ${zone.chlorophyll}</div>
              <div>• <b>Depth:</b> ${zone.depthMeters || 45} m</div>
              <div>• <b>Suitability:</b> ${zone.suitability}</div>
              ${zone.dominantSpecies ? `<div>• <b>Species:</b> ${zone.dominantSpecies.join(", ")}</div>` : ""}
            </div>
            <div style="font-size: 10px; color: #94a3b8; margin-top: 6px; border-top: 1px solid #e2e8f0; padding-top: 4px;">
              INCOIS PFZ Mission / Satellite Delineation
            </div>
          </div>
        `);

        pfzMarker.on("click", () => {
          if (onZoneSelect) onZoneSelect(zone);
        });

        layersRef.current.push(pfzMarker, pfzRadius);
      });
    }

    // 3. Hazard Zones (Polygons)
    if (layersEnabled.hazards) {
      hazardAreas.forEach((hazard) => {
        const polygon = L.polygon(hazard.coordinates, {
          color: "#EF4444",
          fillColor: "#EF4444",
          weight: 2,
          opacity: 0.8,
          fillOpacity: 0.2,
          dashArray: "6, 6",
        }).addTo(map);

        polygon.bindPopup(`
          <div style="font-family: sans-serif; color: #0f172a; min-width: 200px;">
            <div style="font-weight: 700; font-size: 12px; color: #dc2626; margin-bottom: 4px;">🔴 HAZARD ZONE</div>
            <div style="font-size: 13px; font-weight: 600;">${hazard.name}</div>
            <div style="font-size: 11px; color: #475569; margin-top: 4px;">${hazard.description}</div>
            <div style="font-size: 10px; font-weight: 700; color: #dc2626; margin-top: 4px;">Severity: ${hazard.severity}</div>
          </div>
        `);

        layersRef.current.push(polygon);
      });
    }

    // 4. Restricted Areas (Polygons)
    if (layersEnabled.restricted) {
      restrictedAreas.forEach((area) => {
        const polygon = L.polygon(area.coordinates, {
          color: "#475569",
          fillColor: "#334155",
          weight: 2,
          opacity: 0.9,
          fillOpacity: 0.3,
        }).addTo(map);

        polygon.bindPopup(`
          <div style="font-family: sans-serif; color: #0f172a; min-width: 200px;">
            <div style="font-weight: 700; font-size: 12px; color: #475569; margin-bottom: 4px;">⚫ RESTRICTED ZONE</div>
            <div style="font-size: 13px; font-weight: 600;">${area.name}</div>
            <div style="font-size: 11px; color: #475569; margin-top: 4px;">Type: ${area.type}</div>
            <div style="font-size: 10px; color: #64748b; margin-top: 2px;">Authority: Naval / Port Security</div>
          </div>
        `);

        layersRef.current.push(polygon);
      });
    }

    // 5. Active Alert Sector Markers
    if (layersEnabled.alerts) {
      alerts.forEach((alert) => {
        const alertMarker = L.circleMarker([alert.latitude, alert.longitude], {
          radius: 8,
          fillColor: alert.severity === "HIGH" ? "#EF4444" : "#F59E0B",
          color: "#FFFFFF",
          weight: 2,
          opacity: 1,
          fillOpacity: 0.95,
        }).addTo(map);

        alertMarker.bindPopup(`
          <div style="font-family: sans-serif; color: #0f172a; min-width: 190px;">
            <div style="font-weight: 700; font-size: 12px; color: ${alert.severity === 'HIGH' ? '#dc2626' : '#d97706'};">
              ⚠️ ${alert.type} (${alert.severity})
            </div>
            <div style="font-size: 12px; font-weight: 600; margin-top: 2px;">${alert.location}</div>
            <div style="font-size: 11px; color: #475569; margin-top: 3px;">${alert.short_description}</div>
            <div style="font-size: 10px; color: #2563eb; margin-top: 4px; font-weight: 600;">Valid: ${alert.time}</div>
          </div>
        `);

        layersRef.current.push(alertMarker);
      });
    }
  };

  return (
    <div className="relative w-full h-full min-h-[480px] lg:min-h-[580px] rounded-2xl overflow-hidden border border-slate-200 shadow-sm bg-white">
      {/* Map DOM Element */}
      <div ref={mapContainerRef} className="w-full h-full z-10" />

      {/* Map Status Overlay / Header */}
      <div className="absolute top-3 left-12 z-[1000] bg-white/95 backdrop-blur-md border border-slate-200 px-3 py-1.5 rounded-xl text-xs flex items-center space-x-2 text-slate-700 shadow-md">
        <span className="w-2 h-2 rounded-full bg-blue-600 animate-ping"></span>
        <span className="font-bold text-blue-700">GIS Engine:</span>
        <span className="text-slate-600 font-medium">PostGIS / GeoJSON Active</span>
      </div>

      {/* Layer Controls Overlay */}
      <div className="absolute top-3 right-3 z-[1000] bg-white/95 backdrop-blur-md border border-slate-200 px-3 py-1.5 rounded-xl text-xs flex items-center space-x-3 text-slate-700 shadow-md">
        <span className="font-bold text-slate-900 hidden sm:inline">Layers:</span>
        <label className="flex items-center space-x-1.5 cursor-pointer hover:text-blue-700 transition">
          <input
            type="checkbox"
            checked={layersEnabled.pfz}
            onChange={(e) => setLayersEnabled({ ...layersEnabled, pfz: e.target.checked })}
            className="rounded text-blue-600 focus:ring-0 cursor-pointer accent-blue-600"
          />
          <span className="font-medium">PFZ</span>
        </label>
        <label className="flex items-center space-x-1.5 cursor-pointer hover:text-blue-700 transition">
          <input
            type="checkbox"
            checked={layersEnabled.restricted}
            onChange={(e) => setLayersEnabled({ ...layersEnabled, restricted: e.target.checked })}
            className="rounded text-blue-600 focus:ring-0 cursor-pointer accent-blue-600"
          />
          <span className="font-medium">Restricted</span>
        </label>
        <label className="flex items-center space-x-1.5 cursor-pointer hover:text-blue-700 transition">
          <input
            type="checkbox"
            checked={layersEnabled.hazards}
            onChange={(e) => setLayersEnabled({ ...layersEnabled, hazards: e.target.checked })}
            className="rounded text-blue-600 focus:ring-0 cursor-pointer accent-blue-600"
          />
          <span className="font-medium">Hazards</span>
        </label>
      </div>

      {/* Legend Overlay */}
      <MapLegend />
    </div>
  );
};

export default MarineMap;
