"use client";

import React from "react";
import {
  User,
  Anchor,
  Ship,
  Compass,
  Radio,
  ShieldCheck,
  Award,
  Settings,
  Sliders,
  CheckCircle2,
  AlertCircle,
  Clock,
  MapPin,
  FileText,
} from "lucide-react";
import { DataSourcesHealthResponse, RagStatus } from "@/types/marine";

interface ProfileViewProps {
  dataSourcesStatus?: DataSourcesHealthResponse | null;
  ragStatus?: RagStatus | null;
  onNavigateHome?: () => void;
}

export const ProfileView: React.FC<ProfileViewProps> = ({
  dataSourcesStatus,
  ragStatus,
  onNavigateHome,
}) => {
  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      {/* Profile Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-sky-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <User className="w-9 h-9" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl sm:text-2xl font-black text-slate-900">
                Captain Sourabh Wanjari
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Certified Vessel Master
              </span>
            </div>
            <p className="text-sm text-slate-600 font-medium flex flex-wrap items-center gap-2 mt-1">
              <span className="flex items-center gap-1">
                <Ship className="w-4 h-4 text-blue-600" /> MV Sagar Ratna
              </span>
              <span className="text-slate-300">•</span>
              <span className="flex items-center gap-1">
                <MapPin className="w-4 h-4 text-slate-400" /> Port Kasimedu, Chennai
              </span>
              <span className="text-slate-300">•</span>
              <span className="font-mono text-xs text-slate-500">IND-TN-02-MM-1042</span>
            </p>
          </div>
        </div>

        <button
          onClick={onNavigateHome}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold transition shadow-sm cursor-pointer"
        >
          Open Navigation Dashboard
        </button>
      </div>

      {/* Grid of Vessel Details, Safety Certifications, and Navigation Preferences */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Vessel Specifications */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <Ship className="w-4 h-4 text-blue-600" /> Vessel Specifications
            </h2>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
              Mechanized
            </span>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Vessel Category</span>
              <span className="font-semibold text-slate-800">Mechanized Trawler / Gillnetter</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Length Overall (LOA)</span>
              <span className="font-semibold text-slate-800">14.8 meters</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Operational Draft</span>
              <span className="font-semibold text-slate-800">2.6 meters</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Engine Power</span>
              <span className="font-semibold text-slate-800">180 HP Marine Diesel</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Max Endurance</span>
              <span className="font-semibold text-slate-800">7 Days Offshore</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Crew Complement</span>
              <span className="font-semibold text-slate-800">6 Licensed Mariners</span>
            </div>
          </div>
        </div>

        {/* Marine Communications & Regulatory Safety */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <Radio className="w-4 h-4 text-blue-600" /> Communication & Safety
            </h2>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              Compliant
            </span>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">VHF Call Sign</span>
              <span className="font-mono font-bold text-slate-800">8VSR-2026</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Primary Calling Freq</span>
              <span className="font-semibold text-blue-700">Channel 16 (156.8 MHz)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">MMSI Identifier</span>
              <span className="font-mono font-semibold text-slate-800">419002941</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Distress Transponder</span>
              <span className="font-semibold text-emerald-700">406 MHz EPIRB Active</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Life Saving Appliances</span>
              <span className="font-semibold text-slate-800">SOLAS Class-B Approved</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Fishing Moratorium</span>
              <span className="font-semibold text-emerald-600">Season Open (Valid)</span>
            </div>
          </div>
        </div>

        {/* System Intelligence & Gateway Feeds */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <Sliders className="w-4 h-4 text-blue-600" /> Platform Connectivity
            </h2>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
              ORCA Core
            </span>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-50 items-center">
              <span className="text-slate-500">Multi-Agent State</span>
              <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-bold text-[10px]">
                Active (7 Agents)
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50 items-center">
              <span className="text-slate-500">Weather Feed</span>
              <span className="font-semibold text-emerald-700">Open-Meteo LIVE</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50 items-center">
              <span className="text-slate-500">Ocean Feed</span>
              <span className="font-semibold text-emerald-700">Open-Meteo Marine LIVE</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50 items-center">
              <span className="text-slate-500">PFZ Advisories</span>
              <span className="font-semibold text-blue-700">INCOIS Thermal Fronts</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50 items-center">
              <span className="text-slate-500">Knowledge Vector Store</span>
              <span className="font-semibold text-slate-800">
                Chroma ({ragStatus?.total_documents ?? 0} docs indexed)
              </span>
            </div>
            <div className="flex justify-between py-1 items-center">
              <span className="text-slate-500">Geospatial Engine</span>
              <span className="font-semibold text-blue-700">WGS84 GeoJSON / PostGIS Ready</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Preferences Form */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
        <h2 className="font-bold text-slate-900 text-sm flex items-center gap-2 border-b border-slate-100 pb-3">
          <Settings className="w-4 h-4 text-blue-600" /> Maritime Units & Display Preferences
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="space-y-1.5 p-3 rounded-xl bg-slate-50 border border-slate-100">
            <label className="text-slate-500 font-medium">Vessel Speed Unit</label>
            <select className="w-full bg-white border border-slate-200 rounded-lg p-2 font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20">
              <option>Knots (kts) — Standard</option>
              <option>Kilometers per hour (km/h)</option>
            </select>
          </div>

          <div className="space-y-1.5 p-3 rounded-xl bg-slate-50 border border-slate-100">
            <label className="text-slate-500 font-medium">Distance Measurement</label>
            <select className="w-full bg-white border border-slate-200 rounded-lg p-2 font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20">
              <option>Nautical Miles (NM)</option>
              <option>Kilometers (km)</option>
            </select>
          </div>

          <div className="space-y-1.5 p-3 rounded-xl bg-slate-50 border border-slate-100">
            <label className="text-slate-500 font-medium">Sounding & Wave Heights</label>
            <select className="w-full bg-white border border-slate-200 rounded-lg p-2 font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20">
              <option>Meters (m)</option>
              <option>Fathoms (fm)</option>
              <option>Feet (ft)</option>
            </select>
          </div>

          <div className="space-y-1.5 p-3 rounded-xl bg-slate-50 border border-slate-100">
            <label className="text-slate-500 font-medium">Sea Temperature</label>
            <select className="w-full bg-white border border-slate-200 rounded-lg p-2 font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20">
              <option>Celsius (°C)</option>
              <option>Fahrenheit (°F)</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileView;
