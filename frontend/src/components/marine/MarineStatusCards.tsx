import React from "react";
import { CloudSun, Waves, Fish, ShieldAlert } from "lucide-react";
import { MarineConditions, FishingZone, MarineAlert } from "@/types/marine";

interface MarineStatusCardsProps {
  conditions: MarineConditions;
  nearestZone: FishingZone;
  alerts: MarineAlert[];
}

export const MarineStatusCards: React.FC<MarineStatusCardsProps> = ({
  conditions,
  nearestZone,
  alerts,
}) => {
  const highRiskCount = alerts.filter((a) => a.severity === "HIGH").length;
  const overallRisk = highRiskCount > 0 ? "Elevated (Caution)" : "Moderate";

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 my-2">
      {/* 1. Weather Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md hover:border-slate-300 transition">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
            <div className="p-1 rounded-lg bg-sky-50 text-sky-600 border border-sky-100">
              <CloudSun className="w-4 h-4" />
            </div>
            Weather
          </span>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
            Partly Cloudy
          </span>
        </div>
        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Air Temperature:</span>
            <span className="font-bold text-slate-900">{conditions.airTemperature || 29.5}°C</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Wind:</span>
            <span className="font-bold text-slate-900">{conditions.windSpeed} kts ({conditions.windDirection || "ENE"})</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Weather Status:</span>
            <span className="font-semibold text-blue-700">Squall Risk PM</span>
          </div>
        </div>
      </div>

      {/* 2. Ocean Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md hover:border-slate-300 transition">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
            <div className="p-1 rounded-lg bg-blue-50 text-blue-600 border border-blue-100">
              <Waves className="w-4 h-4" />
            </div>
            Ocean Dynamics
          </span>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
            {conditions.seaState}
          </span>
        </div>
        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Wave Height:</span>
            <span className="font-bold text-slate-900">{conditions.waveHeight} m</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Sea Condition:</span>
            <span className="font-bold text-slate-900">{conditions.seaState}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-500">SST:</span>
            <span className="font-bold text-rose-600">{conditions.seaSurfaceTemperature}°C</span>
          </div>
        </div>
      </div>

      {/* 3. Fishing Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md hover:border-slate-300 transition">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
            <div className="p-1 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-100">
              <Fish className="w-4 h-4" />
            </div>
            Fishing Zones
          </span>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            {nearestZone.suitability}
          </span>
        </div>
        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Nearest PFZ:</span>
            <span className="font-bold text-slate-900 truncate max-w-[130px]">{nearestZone.name}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Distance:</span>
            <span className="font-bold text-emerald-700">{nearestZone.distanceKm} km</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Suitability:</span>
            <span className="font-semibold text-emerald-700">{nearestZone.suitability} 🟢</span>
          </div>
        </div>
      </div>

      {/* 4. Safety Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md hover:border-slate-300 transition">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
            <div className="p-1 rounded-lg bg-amber-50 text-amber-600 border border-amber-100">
              <ShieldAlert className="w-4 h-4" />
            </div>
            Navigational Safety
          </span>
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
              highRiskCount > 0
                ? "bg-amber-50 text-amber-700 border border-amber-200"
                : "bg-emerald-50 text-emerald-700 border border-emerald-200"
            }`}
          >
            {overallRisk}
          </span>
        </div>
        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Active Alerts:</span>
            <span className="font-bold text-amber-700">{alerts.length} Bulletins</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-500">High Risk:</span>
            <span className="font-bold text-rose-600">{highRiskCount} Area</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Risk Assessment:</span>
            <span className="font-semibold text-amber-700">Moderate Swell</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarineStatusCards;
