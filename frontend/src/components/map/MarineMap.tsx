"use client";

import React, { useEffect, useRef, useState } from "react";
import "leaflet/dist/leaflet.css";
import {
  FishingZone,
  MarineAlert,
  UserLocation,
  HazardArea,
  RestrictedArea,
  MarineRoute,
} from "@/types/marine";
import MapLegend from "./MapLegend";
import { Layers, Globe, Compass, Route as RouteIcon } from "lucide-react";

interface MarineMapProps {
  userLocation: UserLocation;
  fishingZones: FishingZone[];
  alerts: MarineAlert[];
  hazardAreas: HazardArea[];
  restrictedAreas: RestrictedArea[];
  selectedZoneId?: string | null;
  onZoneSelect?: (zone: FishingZone) => void;
  route?: MarineRoute | null;
}

export const MarineMap: React.FC<MarineMapProps> = ({
  userLocation,
  fishingZones,
  alerts,
  hazardAreas,
  restrictedAreas,
  selectedZoneId,
  onZoneSelect,
  route,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const baseTileLayerRef = useRef<any>(null);
  const layersRef = useRef<any[]>([]);

  // RapidAPI MapTiles configuration with user-provided key
  const RAPIDAPI_KEY =
    process.env.NEXT_PUBLIC_RAPIDAPI_KEY ||
    "e5f367a1d1mshceae8e687637286p187d55jsnab86f1cf2552";
  const RAPIDAPI_HOST =
    process.env.NEXT_PUBLIC_RAPIDAPI_HOST ||
    "maptiles.p.rapidapi.com";

  // Basemap state: RapidAPI Satellite (Bathymetric Topo) vs ESRI Aerial
  // Standard map has been removed per user request
  const [basemap, setBasemap] = useState<"satellite" | "esri">("satellite");

  const [layersEnabled, setLayersEnabled] = useState({
    pfz: true,
    restricted: true,
    hazards: true,
    alerts: true,
    route: true,
  });

  // 1. Initialize Leaflet Map
  useEffect(() => {
    let isMounted = true;

    async function initMap() {
      if (!mapContainerRef.current || mapInstanceRef.current) return;

      const L = (await import("leaflet")).default;

      // Fix default marker icon paths in Next.js
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      // Default map center
      const centerLat = route?.origin?.latitude || userLocation.latitude;
      const centerLon = route?.origin?.longitude ? route.origin.longitude + 0.1 : userLocation.longitude + 0.15;

      const map = L.map(mapContainerRef.current, {
        center: [centerLat, centerLon],
        zoom: route ? 11 : 10,
        minZoom: 4,
        maxZoom: 19,
        zoomControl: false,
      });

      // Position zoom controls in top-left
      L.control.zoom({ position: "topleft" }).addTo(map);

      // Initial Base Tile Layer (RapidAPI Satellite by default)
      let baseLayer;
      if (basemap === "esri") {
        baseLayer = L.tileLayer(
          "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
          {
            attribution:
              "Tiles &copy; Esri &mdash; Source: Esri, USGS, NOAA",
            maxZoom: 18,
          }
        );
      } else {
        baseLayer = L.tileLayer(
          `https://${RAPIDAPI_HOST}/en/map/v1/{z}/{x}/{y}.png?rapidapi-key=${RAPIDAPI_KEY}`,
          {
            attribution:
              '&copy; <a href="https://www.maptilesapi.com" target="_blank" rel="noopener noreferrer">MapTiles API</a> &copy; <a href="https://rapidapi.com" target="_blank" rel="noopener noreferrer">RapidAPI</a>',
            maxZoom: 19,
          }
        );
      }
      baseLayer.addTo(map);

      baseTileLayerRef.current = baseLayer;
      mapInstanceRef.current = map;

      // Draw all feature layers
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

  // 2. Basemap Layer Switcher (RapidAPI Satellite <-> ESRI Aerial)
  useEffect(() => {
    if (!mapInstanceRef.current) return;

    import("leaflet").then((L) => {
      const map = mapInstanceRef.current;
      if (baseTileLayerRef.current) {
        map.removeLayer(baseTileLayerRef.current);
      }

      if (basemap === "esri") {
        baseTileLayerRef.current = L.default.tileLayer(
          "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
          {
            attribution:
              "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
            maxZoom: 18,
          }
        ).addTo(map);
      } else {
        baseTileLayerRef.current = L.default.tileLayer(
          `https://${RAPIDAPI_HOST}/en/map/v1/{z}/{x}/{y}.png?rapidapi-key=${RAPIDAPI_KEY}`,
          {
            attribution:
              '&copy; <a href="https://www.maptilesapi.com" target="_blank" rel="noopener noreferrer">MapTiles API</a> &copy; <a href="https://rapidapi.com" target="_blank" rel="noopener noreferrer">RapidAPI</a>',
            maxZoom: 19,
          }
        ).addTo(map);
      }
    });
  }, [basemap]);

  // 3. Re-render layers when props, route, or layer toggles change
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    import("leaflet").then((L) => {
      renderLayers(L.default, mapInstanceRef.current);
    });
  }, [fishingZones, alerts, hazardAreas, restrictedAreas, selectedZoneId, layersEnabled, route]);

  // Layer rendering engine
  const renderLayers = (L: any, map: any) => {
    // Clear previous vector layers
    layersRef.current.forEach((layer) => layer.remove());
    layersRef.current = [];

    // --- 1. User Position Marker ---
    const userMarker = L.circleMarker([userLocation.latitude, userLocation.longitude], {
      radius: 9,
      fillColor: "#2563EB",
      color: "#FFFFFF",
      weight: 2,
      opacity: 1,
      fillOpacity: 0.95,
    }).addTo(map);

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

    // --- 2. Potential Fishing Zones (PFZ) ---
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

        const pfzMarker = L.circleMarker([zone.latitude, zone.longitude], {
          radius: 11,
          fillColor: fillColor,
          color: "#FFFFFF",
          weight: 2,
          opacity: 1,
          fillOpacity: 0.9,
        }).addTo(map);

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
            </div>
          </div>
        `);

        layersRef.current.push(pfzMarker, pfzRadius);
      });
    }

    // --- 3. Restricted Zones (Naval / MPAs) ---
    if (layersEnabled.restricted) {
      restrictedAreas.forEach((area) => {
        const polygon = L.polygon(area.coordinates, {
          color: "#7C3AED",
          weight: 2,
          opacity: 0.8,
          fillColor: "#8B5CF6",
          fillOpacity: 0.22,
          dashArray: "6, 6",
        }).addTo(map);

        polygon.bindPopup(`
          <div style="font-family: sans-serif; color: #0f172a; min-width: 200px;">
            <div style="font-weight: 700; font-size: 12px; color: #6d28d9;">🚫 Restricted Fairway</div>
            <div style="font-size: 12px; font-weight: 600; margin-top: 2px;">${area.name}</div>
            <div style="font-size: 11px; color: #475569; margin-top: 3px;">${area.description}</div>
          </div>
        `);

        layersRef.current.push(polygon);
      });
    }

    // --- 4. Hazard Polygons ---
    if (layersEnabled.hazards) {
      hazardAreas.forEach((hazard) => {
        const polygon = L.polygon(hazard.coordinates, {
          color: "#EF4444",
          weight: 2,
          opacity: 0.85,
          fillColor: "#DC2626",
          fillOpacity: 0.25,
        }).addTo(map);

        polygon.bindPopup(`
          <div style="font-family: sans-serif; color: #0f172a; min-width: 200px;">
            <div style="font-weight: 700; font-size: 12px; color: #dc2626;">⚠️ Active Hazard Sector</div>
            <div style="font-size: 12px; font-weight: 600; margin-top: 2px;">${hazard.name}</div>
            <div style="font-size: 11px; color: #475569; margin-top: 3px;">${hazard.description}</div>
          </div>
        `);

        layersRef.current.push(polygon);
      });
    }

    // --- 5. Active Alerts ---
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
            <div style="font-weight: 700; font-size: 12px; color: ${alert.severity === "HIGH" ? "#dc2626" : "#d97706"};">
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

    // --- 6. Recommended Short & Safe Marine Route Track ---
    if (route && route.waypoints && route.waypoints.length >= 2 && layersEnabled.route) {
      const latLngs = route.waypoints.map((pt) => [pt[0], pt[1]]);

      // Outer luminous glow line
      const glowLine = L.polyline(latLngs, {
        color: "#0284c7",
        weight: 8,
        opacity: 0.45,
        lineCap: "round",
        lineJoin: "round",
      }).addTo(map);

      // Core route polyline
      const routeLine = L.polyline(latLngs, {
        color: "#06b6d4",
        weight: 4.5,
        opacity: 0.95,
        dashArray: "10, 6",
        lineCap: "round",
        lineJoin: "round",
      }).addTo(map);

      // Origin Marker (Green Pin)
      const originPt = route.waypoints[0];
      const originMarker = L.circleMarker([originPt[0], originPt[1]], {
        radius: 10,
        fillColor: "#10B981",
        color: "#FFFFFF",
        weight: 3,
        opacity: 1,
        fillOpacity: 0.95,
      }).addTo(map);

      originMarker.bindPopup(`
        <div style="font-family: sans-serif; color: #0f172a; min-width: 180px;">
          <div style="font-weight: 700; font-size: 13px; color: #059669; margin-bottom: 2px;">🟢 Route Departure (Origin)</div>
          <div style="font-size: 12px; font-weight: 600;">${route.origin.name || "Origin Port"}</div>
          <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Lat: ${originPt[0].toFixed(3)}°, Lon: ${originPt[1].toFixed(3)}°</div>
        </div>
      `);

      // Destination Marker (Amber/Red Pin)
      const destPt = route.waypoints[route.waypoints.length - 1];
      const destMarker = L.circleMarker([destPt[0], destPt[1]], {
        radius: 10,
        fillColor: "#F59E0B",
        color: "#FFFFFF",
        weight: 3,
        opacity: 1,
        fillOpacity: 0.95,
      }).addTo(map);

      destMarker.bindPopup(`
        <div style="font-family: sans-serif; color: #0f172a; min-width: 190px;">
          <div style="font-weight: 700; font-size: 13px; color: #d97706; margin-bottom: 2px;">🏁 Route Arrival (Destination)</div>
          <div style="font-size: 12px; font-weight: 600;">${route.destination.name || "Destination Port"}</div>
          <div style="font-size: 11px; color: #475569; margin-top: 2px;">Total: <b>${route.distance_km} km</b> • Est: <b>${route.estimated_duration_text}</b></div>
          <div style="font-size: 11px; color: #059669; font-weight: 600; margin-top: 2px;">Safety Score: <b>${route.safety_score}/100</b> (${route.risk_level})</div>
        </div>
      `);

      layersRef.current.push(glowLine, routeLine, originMarker, destMarker);

      // Auto-fit map viewport to encompass the entire recommended route
      try {
        const bounds = routeLine.getBounds();
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [60, 60], maxZoom: 13 });
        }
      } catch (e) {
        console.warn("[MarineMap] Could not auto-fit route bounds:", e);
      }
    }
  };

  return (
    <div className="relative w-full h-full min-h-[480px] lg:min-h-[580px] rounded-2xl overflow-hidden border border-slate-700/60 shadow-xl bg-slate-950">
      {/* Map DOM Element */}
      <div ref={mapContainerRef} className="w-full h-full z-10" />

      {/* Top Left: GIS Engine Status + Active Basemap Indicator */}
      <div className="absolute top-3 left-12 z-[1000] flex items-center gap-2">
        <div className="bg-slate-900/90 backdrop-blur-md border border-slate-700/80 px-3 py-1.5 rounded-xl text-xs flex items-center space-x-2 text-slate-200 shadow-md">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
          <span className="font-bold text-cyan-300">GIS Engine:</span>
          <span className="text-slate-300 font-medium">PostGIS / GeoJSON Active</span>
        </div>

        {/* Satellite Basemap Switcher: [🛰️ RapidAPI Satellite] [ESRI Aerial] */}
        <div className="bg-slate-900/95 backdrop-blur-md border border-slate-700/90 p-0.5 rounded-xl flex items-center shadow-md">
          <button
            type="button"
            onClick={() => setBasemap("satellite")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition cursor-pointer ${
              basemap === "satellite"
                ? "bg-cyan-600 text-white shadow-xs"
                : "text-slate-400 hover:text-white"
            }`}
            title="RapidAPI Satellite & Ocean Bathymetric Topography (Integrated API Key)"
          >
            <Globe className="w-3.5 h-3.5" />
            <span>RapidAPI Satellite</span>
            <span className="text-[9px] bg-cyan-950 text-cyan-300 font-bold px-1.5 py-0.5 rounded border border-cyan-500/40">
              Active
            </span>
          </button>
          <button
            type="button"
            onClick={() => setBasemap("esri")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition cursor-pointer ${
              basemap === "esri"
                ? "bg-indigo-600 text-white shadow-xs"
                : "text-slate-400 hover:text-white"
            }`}
            title="ESRI High-Resolution Optical Earth Imagery"
          >
            <Globe className="w-3.5 h-3.5" />
            <span>ESRI Aerial</span>
          </button>
        </div>
      </div>

      {/* Top Right: Layer Controls */}
      <div className="absolute top-3 right-3 z-[1000] bg-slate-900/90 backdrop-blur-md border border-slate-700/80 px-3 py-1.5 rounded-xl text-xs flex items-center space-x-3 text-slate-200 shadow-md">
        <span className="font-bold text-cyan-300 hidden sm:inline flex items-center gap-1">
          <Layers className="w-3.5 h-3.5" />
          Layers:
        </span>
        {route && (
          <label className="flex items-center space-x-1.5 cursor-pointer hover:text-cyan-300 transition">
            <input
              type="checkbox"
              checked={layersEnabled.route}
              onChange={(e) => setLayersEnabled({ ...layersEnabled, route: e.target.checked })}
              className="rounded text-cyan-500 focus:ring-0 cursor-pointer accent-cyan-500"
            />
            <span className="font-semibold text-cyan-300">Route</span>
          </label>
        )}
        <label className="flex items-center space-x-1.5 cursor-pointer hover:text-cyan-300 transition">
          <input
            type="checkbox"
            checked={layersEnabled.pfz}
            onChange={(e) => setLayersEnabled({ ...layersEnabled, pfz: e.target.checked })}
            className="rounded text-blue-500 focus:ring-0 cursor-pointer accent-blue-500"
          />
          <span className="font-medium">PFZ</span>
        </label>
        <label className="flex items-center space-x-1.5 cursor-pointer hover:text-cyan-300 transition">
          <input
            type="checkbox"
            checked={layersEnabled.restricted}
            onChange={(e) => setLayersEnabled({ ...layersEnabled, restricted: e.target.checked })}
            className="rounded text-purple-500 focus:ring-0 cursor-pointer accent-purple-500"
          />
          <span className="font-medium">Restricted</span>
        </label>
        <label className="flex items-center space-x-1.5 cursor-pointer hover:text-cyan-300 transition">
          <input
            type="checkbox"
            checked={layersEnabled.hazards}
            onChange={(e) => setLayersEnabled({ ...layersEnabled, hazards: e.target.checked })}
            className="rounded text-red-500 focus:ring-0 cursor-pointer accent-red-500"
          />
          <span className="font-medium">Hazards</span>
        </label>
      </div>

      {/* Floating Route Summary Overlay (if route active) */}
      {route && (
        <div className="absolute bottom-4 left-4 z-[1000] bg-slate-900/95 backdrop-blur-md border border-cyan-500/50 rounded-xl p-3 shadow-xl max-w-sm sm:max-w-md text-xs space-y-1.5 text-slate-200">
          <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-1.5">
            <div className="flex items-center gap-1.5 font-bold text-white text-sm">
              <RouteIcon className="w-4 h-4 text-cyan-400" />
              <span>
                {route.origin.name || "Origin"} ➔ {route.destination.name || "Destination"}
              </span>
            </div>
            <span
              className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${
                route.safety_score >= 80
                  ? "bg-emerald-950/80 text-emerald-300 border-emerald-700/60"
                  : route.safety_score >= 50
                  ? "bg-amber-950/80 text-amber-300 border-amber-700/60"
                  : "bg-red-950/80 text-red-300 border-red-700/60"
              }`}
            >
              Score: {route.safety_score}/100 ({route.risk_level})
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300 pt-0.5">
            <div>
              <span className="text-slate-400">Distance:</span> <strong>{route.distance_km} km</strong>
            </div>
            <div>
              <span className="text-slate-400">Duration:</span> <strong>{route.estimated_duration_text}</strong>
            </div>
            {route.route_conditions?.avg_wind_speed_knots !== undefined && (
              <div>
                <span className="text-slate-400">Avg Wind:</span> <strong>{route.route_conditions.avg_wind_speed_knots} kts</strong>
              </div>
            )}
            {route.route_conditions?.max_wave_height_m !== undefined && (
              <div>
                <span className="text-slate-400">Max Wave:</span> <strong>{route.route_conditions.max_wave_height_m} m</strong>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Legend Overlay */}
      <MapLegend />
    </div>
  );
};

export default MarineMap;
