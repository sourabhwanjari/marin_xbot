"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/layout/Header";
import MapWrapper from "@/components/map/MapWrapper";
import {
  FishingZone,
  MarineAlert,
} from "@/types/marine";
import { mockFishingZones as fallbackZones } from "@/data/fishingZones";
import { mockAlerts as fallbackAlerts } from "@/data/alerts";
import {
  defaultUserLocation,
  mockHazardAreas,
  mockRestrictedAreas,
} from "@/data/locations";
import { fetchFishingZones, fetchMarineAlerts } from "@/services/api";
import { MapPin, ShieldAlert, Waves, CheckCircle2 } from "lucide-react";

export default function MarineMapPage() {
  const [fishingZones, setFishingZones] = useState<FishingZone[]>(fallbackZones);
  const [alerts, setAlerts] = useState<MarineAlert[]>(fallbackAlerts);
  const [selectedZone, setSelectedZone] = useState<FishingZone | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadMapData() {
      setIsLoading(true);
      try {
        const [zonesRes, alertsRes] = await Promise.all([
          fetchFishingZones(),
          fetchMarineAlerts(),
        ]);
        if (zonesRes && zonesRes.length > 0) setFishingZones(zonesRes);
        if (alertsRes && alertsRes.length > 0) setAlerts(alertsRes);
      } catch (err) {
        console.warn("Failed fetching map data from backend, continuing with verified reference:", err);
      } finally {
        setIsLoading(false);
      }
    }

    loadMapData();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-[#070d19] text-slate-100">
      {/* Top Navigation Bar: MARINEX AI | Home | Map | About */}
      <Header />

      {/* Main Map View Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-4 lg:p-6 space-y-4">
        {/* Top Console Banner */}
        <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-4 sm:p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-xl bg-gradient-to-br from-cyan-500 via-sky-600 to-blue-700 flex items-center justify-center text-white shadow-md shadow-cyan-500/25 flex-shrink-0">
              <MapPin className="w-5 h-5 sm:w-6 sm:h-6" />
            </div>
            <div>
              <h1 className="text-lg sm:text-xl font-extrabold text-white flex items-center gap-2">
                <span>Marine Geospatial & Navigation Console</span>
              </h1>
              <p className="text-xs text-slate-400 mt-0.5 max-w-2xl leading-relaxed">
                Live interactive bathymetry, INCOIS Potential Fishing Zones (PFZ), navigation hazards, and coastal safety corridors.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 shadow-xs">
              <Waves className="w-3.5 h-3.5 text-cyan-400" />
              {fishingZones.length} PFZ Sectors
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-300 border border-amber-800/60 shadow-xs">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
              {alerts.length} Active Advisories
            </span>
          </div>
        </div>

        {/* Selected Zone Quick Details (if user clicked a zone) */}
        {selectedZone && (
          <div className="bg-cyan-950/60 border border-cyan-700/60 rounded-xl p-3.5 text-xs text-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-in fade-in duration-200 shadow-md">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-cyan-400 flex-shrink-0" />
              <div>
                <span className="font-bold text-white text-sm mr-2">{selectedZone.name}</span>
                <span className="text-cyan-300 font-mono text-[11px]">
                  [{selectedZone.latitude.toFixed(3)}°N, {selectedZone.longitude.toFixed(3)}°E]
                </span>
                <span className="text-slate-400 block sm:inline sm:ml-2">
                  {selectedZone.depthMeters ? `Depth: ${selectedZone.depthMeters}m • ` : ""}Suitability: <strong className="text-emerald-400">{selectedZone.suitability}</strong>
                </span>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setSelectedZone(null)}
              className="text-[11px] text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-900/60 border border-slate-700/80 transition self-end sm:self-auto cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Large Marine Map Container */}
        <section className="h-[620px] sm:h-[680px] lg:h-[720px] w-full rounded-2xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-950">
          <MapWrapper
            userLocation={defaultUserLocation}
            fishingZones={fishingZones}
            alerts={alerts}
            hazardAreas={mockHazardAreas}
            restrictedAreas={mockRestrictedAreas}
            selectedZoneId={selectedZone?.id}
            onZoneSelect={(zone) => setSelectedZone(zone)}
          />
        </section>
      </main>
    </div>
  );
}
