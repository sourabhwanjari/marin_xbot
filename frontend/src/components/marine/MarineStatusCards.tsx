import React from "react";
import { CloudSun, Waves, Fish, ShieldAlert, Wind, Thermometer, Compass } from "lucide-react";
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
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 my-4">
      {/* 1. Weather Card */}
      <div className="bg-marine-900/90 backdrop-blur-md rounded-xl border border-cyan-500/20 p-3.5 shadow-marine-card hover:border-cyan-500/40 transition">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <CloudSun className="w-4 h-4 text-cyan-400" /> Weather
          </span>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
            Partly Cloudy
          </span>
        </div>
        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between items-center text-slate-300">
            <span className="text-slate-400">Air Temperature:</span>
            <span className="font-bold text-white">{conditions.airTemperature || 29.5}°C</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="text-slate-400">Wind:</span>
            <span className="font-bold text-white">{conditions.windSpeed} kts ({conditions.windDirection || "ENE"})</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="text-slate-400">Weather Status:</span>
            <span className="font-bold text-cyan-300">Squall Risk PM</span>
          </div>
        </div>
      </div>

      {/* 2. Ocean Card */}
      <div className="bg-marine-900/90 backdrop-blur-md rounded-xl border border-cyan-500/20 p-3.5 shadow-marine-card hover:border-cyan-500/40 transition">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <Waves className="w-4 h-4 text-blue-400" /> Ocean
          </span>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/40">
            {conditions.seaState}
          </span>
        </div>
        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between items-center text-slate-300">
            <span className="text-slate-400">Wave Height:</span>
            <span className="font-bold text-white">{conditions.waveHeight} m</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="text-slate-400">Sea Condition:</span>
            <span className="font-bold text-white">{conditions.seaState}</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="text-slate-400">SST:</span>
            <span className="font-bold text-rose-300">{conditions.seaSurfaceTemperature}°C</span>
          </div>
        </div>
      </div>

      {/* 3. Fishing Card */}
      <div className="bg-marine-900/90 backdrop-blur-md rounded-xl border border-cyan-500/20 p-3.5 shadow-marine-card hover:border-cyan-500/40 transition">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <Fish className="w-4 h-4 text-emerald-400" /> Fishing
          </span>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
            {nearestZone.suitability}
          </span>
        </div>
        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between items-center text-slate-300">
            <span className="text-slate-400">Nearest PFZ:</span>
            <span className="font-bold text-white truncate max-w-[130px]">{nearestZone.name}</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="text-slate-400">Distance:</span>
            <span className="font-bold text-emerald-300">{nearestZone.distanceKm} km</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="text-slate-400">Suitability:</span>
            <span className="font-bold text-emerald-400">{nearestZone.suitability} 🟢</span>
          </div>
        </div>
      </div>

      {/* 4. Safety Card */}
      <div className="bg-marine-900/90 backdrop-blur-md rounded-xl border border-cyan-500/20 p-3.5 shadow-marine-card hover:border-cyan-500/40 transition">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-amber-400" /> Safety
          </span>
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
              highRiskCount > 0
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
            }`}
          >
            {overallRisk}
          </span>
        </div>
        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between items-center text-slate-300">
            <span className="text-slate-400">Active Alerts:</span>
            <span className="font-bold text-amber-300">{alerts.length} Bulletins</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="text-slate-400">High Risk:</span>
            <span className="font-bold text-rose-400">{highRiskCount} Area</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="text-slate-400">Risk Level:</span>
            <span className="font-bold text-amber-300">Moderate Swell</span>
          </div>
        </div>
      </div>
    </div>
  );
};
export default MarineStatusCards;
