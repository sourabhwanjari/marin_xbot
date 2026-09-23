"use client";

import React, { useState, useEffect } from "react";
import Header, { NavTab } from "@/components/layout/Header";
import MapWrapper from "@/components/map/MapWrapper";
import ChatPanel from "@/components/chat/ChatPanel";
import MarineStatusCards from "@/components/marine/MarineStatusCards";
import MarineConditionCard from "@/components/marine/MarineConditionCard";
import FishingZoneCard from "@/components/marine/FishingZoneCard";
import SafetyCard from "@/components/marine/SafetyCard";
import AlertPanel from "@/components/alerts/AlertPanel";
import KnowledgeModal from "@/components/knowledge/KnowledgeModal";
import ProfileView from "@/components/profile/ProfileView";

import {
  MarineConditions,
  FishingZone,
  MarineAlert,
  RagStatus,
  DataSourcesHealthResponse,
} from "@/types/marine";
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
import { ShieldAlert, Waves, Radio, Anchor, PhoneCall, LifeBuoy } from "lucide-react";

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
  const [activeTab, setActiveTab] = useState<NavTab>("home");

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
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      {/* Top Navigation Bar: | Home | Safety Info | Sea Info | Profile | */}
      <Header
        systemStatus={systemStatus}
        isDemo={true}
        ragStatus={ragStatus}
        dataSourcesStatus={dataSourcesStatus}
        onOpenKnowledgeModal={() => setIsKnowledgeModalOpen(true)}
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-4 lg:p-6 space-y-5">
        {/* ==================== TAB 1: HOME VIEW ==================== */}
        {activeTab === "home" && (
          <div className="space-y-5 animate-in fade-in duration-200">
            {/* 2-Column Responsive Layout: LEFT = CHATBOT, RIGHT = MAP */}
            <section className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
              {/* Left Column: Simple Marine Intelligence Chatbot (5 cols on desktop) */}
              <div className="lg:col-span-5 flex flex-col min-h-[480px] lg:min-h-[580px]">
                <ChatPanel
                  onActionSelect={(action) => {
                    if (action.includes("Zone Alpha")) {
                      const z = fishingZones.find((x) => x.id === "pfz-01");
                      if (z) setSelectedZone(z);
                    }
                  }}
                />
              </div>

              {/* Right Column: Interactive Marine Map (7 cols on desktop) */}
              <div className="lg:col-span-7 flex flex-col min-h-[480px] lg:min-h-[580px]">
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
            </section>

            {/* Compact Marine Status Cards Overview (Weather, Ocean, Fishing, Safety) */}
            <section>
              <MarineStatusCards
                conditions={conditions}
                nearestZone={nearestZone}
                alerts={alerts}
              />
            </section>
          </div>
        )}

        {/* ==================== TAB 2: SAFETY INFO VIEW ==================== */}
        {activeTab === "safety" && (
          <div className="space-y-5 animate-in fade-in duration-200">
            {/* Safety Overview Banner */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center">
                  <ShieldAlert className="w-7 h-7" />
                </div>
                <div>
                  <h1 className="text-xl font-black text-slate-900">Maritime Safety & Emergency Information</h1>
                  <p className="text-xs text-slate-500 font-medium mt-0.5">
                    Real-time weather bulletins, high wave warnings, emergency frequencies, and coastal safety corridors.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
                  {alerts.length} Active Advisories
                </span>
              </div>
            </div>

            {/* Active Alerts Panel */}
            <section>
              <AlertPanel alerts={alerts} />
            </section>

            {/* Emergency Contacts & Protocol Guidelines */}
            <section className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
                <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm border-b border-slate-100 pb-2.5">
                  <Radio className="w-4 h-4 text-blue-600" />
                  <span>VHF Emergency Frequencies</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-50">
                    <span className="text-slate-500">Distress & Calling:</span>
                    <span className="font-bold text-rose-600">Channel 16 (156.8 MHz)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-50">
                    <span className="text-slate-500">Port Operations:</span>
                    <span className="font-bold text-slate-800">Channel 12 / 14</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Coast Guard Working:</span>
                    <span className="font-bold text-blue-700">Channel 06 / 08</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
                <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm border-b border-slate-100 pb-2.5">
                  <PhoneCall className="w-4 h-4 text-emerald-600" />
                  <span>Emergency Helplines</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-50">
                    <span className="text-slate-500">Indian Coast Guard:</span>
                    <span className="font-bold text-slate-900">1554 (Toll Free)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-50">
                    <span className="text-slate-500">Coastal Police:</span>
                    <span className="font-bold text-slate-900">1093</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Fisheries Control Room:</span>
                    <span className="font-bold text-slate-900">044-25951800</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
                <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm border-b border-slate-100 pb-2.5">
                  <LifeBuoy className="w-4 h-4 text-sky-600" />
                  <span>Heavy Weather Checklist</span>
                </div>
                <ul className="space-y-1.5 text-xs text-slate-600">
                  <li className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                    <span>Life jackets donned by all crew members</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                    <span>Hatch covers & bilge pumps secured</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                    <span>Navigational lights tested & operational</span>
                  </li>
                </ul>
              </div>
            </section>
          </div>
        )}

        {/* ==================== TAB 3: SEA INFO VIEW ==================== */}
        {activeTab === "sea" && (
          <div className="space-y-5 animate-in fade-in duration-200">
            {/* Sea Info Overview Banner */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center">
                  <Waves className="w-7 h-7" />
                </div>
                <div>
                  <h1 className="text-xl font-black text-slate-900">Oceanographic Telemetry & Fishing Zones</h1>
                  <p className="text-xs text-slate-500 font-medium mt-0.5">
                    Live Sea Surface Temperature (SST), Chlorophyll-a fronts, wave dynamics, and INCOIS Potential Fishing Zones.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  Open-Meteo & INCOIS Synced
                </span>
              </div>
            </div>

            {/* Oceanographic Telemetry Panel */}
            <section>
              <MarineConditionCard conditions={conditions} />
            </section>

            {/* Potential Fishing Zones Cards Grid */}
            <section className="space-y-3">
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                Potential Fishing Zones (PFZ Sectors)
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {fishingZones.map((zone) => (
                  <FishingZoneCard key={zone.id} zone={zone} />
                ))}
              </div>
            </section>
          </div>
        )}

        {/* ==================== TAB 4: PROFILE VIEW ==================== */}
        {activeTab === "profile" && (
          <div className="animate-in fade-in duration-200">
            <ProfileView
              dataSourcesStatus={dataSourcesStatus}
              ragStatus={ragStatus}
              onNavigateHome={() => setActiveTab("home")}
            />
          </div>
        )}
      </main>

      {/* Knowledge Base Modal */}
      <KnowledgeModal
        isOpen={isKnowledgeModalOpen}
        onClose={() => setIsKnowledgeModalOpen(false)}
        status={ragStatus}
        onStatusUpdate={(st) => setRagStatus(st)}
      />

      {/* Professional White Footer */}
      <footer className="w-full border-t border-slate-200 bg-white py-3.5 px-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <span className="font-bold text-slate-800">MARINEX AI</span> — Built for{" "}
            <span className="text-blue-600 font-medium">
              ORCA: Marine EcOsystem Reasoning with Collaborative Agents
            </span>
          </div>
          <div className="flex items-center space-x-3 text-[11px] text-slate-500 font-mono">
            <span>Phase 4: Real Marine Data + Geo-Spatial Intelligence</span>
            <span>•</span>
            <span className="text-blue-700 font-semibold">Open-Meteo & INCOIS Feeds</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
