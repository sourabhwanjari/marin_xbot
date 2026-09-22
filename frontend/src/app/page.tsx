"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/layout/Header";
import MapWrapper from "@/components/map/MapWrapper";
import ChatPanel from "@/components/chat/ChatPanel";
import MarineStatusCards from "@/components/marine/MarineStatusCards";
import MarineConditionCard from "@/components/marine/MarineConditionCard";
import AlertPanel from "@/components/alerts/AlertPanel";
import KnowledgeModal from "@/components/knowledge/KnowledgeModal";

import { MarineConditions, FishingZone, MarineAlert, RagStatus, DataSourcesHealthResponse } from "@/types/marine";
import { marineConditions as fallbackConditions } from "@/data/marineData";
import { mockFishingZones as fallbackZones } from "@/data/fishingZones";
import { mockAlerts as fallbackAlerts } from "@/data/alerts";
import { defaultUserLocation, mockHazardAreas, mockRestrictedAreas } from "@/data/locations";
import {
  fetchHealth,
  fetchMarineConditions,
  fetchFishingZones,
  fetchMarineAlerts,
  fetchRagStatus,
  fetchDataSourcesStatus,
} from "@/services/api";

export default function DashboardPage() {
  const [conditions, setConditions] = useState<MarineConditions>(fallbackConditions);
  const [fishingZones, setFishingZones] = useState<FishingZone[]>(fallbackZones);
  const [alerts, setAlerts] = useState<MarineAlert[]>(fallbackAlerts);
  const [selectedZone, setSelectedZone] = useState<FishingZone | null>(null);
  const [systemStatus, setSystemStatus] = useState("Operational");
  const [ragStatus, setRagStatus] = useState<RagStatus | null>(null);
  const [dataSourcesStatus, setDataSourcesStatus] = useState<DataSourcesHealthResponse | null>(null);
  const [isKnowledgeModalOpen, setIsKnowledgeModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const [healthRes, condRes, zonesRes, alertsRes, ragRes, feedsRes] = await Promise.all([
          fetchHealth(),
          fetchMarineConditions(),
          fetchFishingZones(),
          fetchMarineAlerts(),
          fetchRagStatus(),
          fetchDataSourcesStatus(),
        ]);

        if (healthRes && healthRes.status === "ok") {
          setSystemStatus("Operational");
        }
        if (condRes) setConditions(condRes);
        if (zonesRes && zonesRes.length > 0) setFishingZones(zonesRes);
        if (alertsRes && alertsRes.length > 0) setAlerts(alertsRes);
        if (ragRes) setRagStatus(ragRes);
        if (feedsRes) setDataSourcesStatus(feedsRes);
      } catch (err) {
        console.warn("Failed fetching from backend, continuing with mock data:", err);
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, []);

  const nearestZone = fishingZones[0] || fallbackZones[0];

  return (
    <div className="min-h-screen flex flex-col bg-marine-950 text-slate-100">
      {/* Top Navigation with Knowledge Base & Data Feeds Trigger */}
      <Header
        systemStatus={systemStatus}
        isDemo={true}
        ragStatus={ragStatus}
        dataSourcesStatus={dataSourcesStatus}
        onOpenKnowledgeModal={() => setIsKnowledgeModalOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-4 lg:p-6 space-y-4">
        {/* Main Dashboard Section: 2-Column Responsive Layout */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
          {/* Left Column: Interactive Marine Map (7 cols on desktop) */}
          <div className="lg:col-span-7 flex flex-col min-h-[460px] lg:min-h-[560px]">
            <MapWrapper
              userLocation={defaultUserLocation}
              fishingZones={fishingZones}
              alerts={alerts}
              hazardAreas={mockHazardAreas}
              restrictedAreas={mockRestrictedAreas}
              selectedZoneId={selectedZone?.id}
              onZoneSelect={(zone) => setSelectedZone(zone)}
            />
          </div>

          {/* Right Column: AI Marine Intelligence Panel (5 cols on desktop) */}
          <div className="lg:col-span-5 flex flex-col min-h-[460px] lg:min-h-[560px]">
            <ChatPanel
              onActionSelect={(action) => {
                if (action.includes("Zone Alpha")) {
                  const z = fishingZones.find((x) => x.id === "pfz-01");
                  if (z) setSelectedZone(z);
                }
              }}
            />
          </div>
        </section>

        {/* Compact Marine Status Cards (Weather, Ocean, Fishing, Safety) */}
        <section>
          <MarineStatusCards
            conditions={conditions}
            nearestZone={nearestZone}
            alerts={alerts}
          />
        </section>

        {/* Marine Conditions Telemetry Panel */}
        <section>
          <MarineConditionCard conditions={conditions} />
        </section>

        {/* Active Marine Alerts Section */}
        <section>
          <AlertPanel alerts={alerts} />
        </section>
      </main>

      {/* Knowledge Base Modal */}
      <KnowledgeModal
        isOpen={isKnowledgeModalOpen}
        onClose={() => setIsKnowledgeModalOpen(false)}
        status={ragStatus}
        onStatusUpdate={(st) => setRagStatus(st)}
      />

      {/* Compact Marine-Tech Footer */}
      <footer className="w-full border-t border-slate-800/80 bg-marine-900/60 py-3 px-4 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <span className="font-bold text-slate-300">MARINEX AI</span> — Built for{" "}
            <span className="text-cyan-400 font-medium">
              ORCA: Marine EcOsystem Reasoning with Collaborative Agents
            </span>
          </div>
          <div className="flex items-center space-x-3 text-[11px] text-slate-400 font-mono">
            <span>Phase 4: Real Marine Data + Geo-Spatial Intelligence Active</span>
            <span>•</span>
            <span className="text-cyan-400 font-semibold">Open-Meteo & INCOIS Feeds</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
