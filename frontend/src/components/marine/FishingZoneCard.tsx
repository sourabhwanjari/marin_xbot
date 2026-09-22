import React from "react";
import { Compass, Navigation, Fish } from "lucide-react";
import { FishingZone } from "@/types/marine";

interface FishingZoneCardProps {
  zone: FishingZone;
}

export const FishingZoneCard: React.FC<FishingZoneCardProps> = ({ zone }) => {
  return (
    <div className="bg-marine-850/80 border border-slate-700/60 rounded-xl p-3.5 hover:border-emerald-500/40 transition">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
          <Fish className="w-3.5 h-3.5 text-emerald-400" /> Fishing Intelligence
        </span>
        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
          {zone.suitability}
        </span>
      </div>

      <div className="text-sm font-bold text-white truncate mb-1">
        {zone.name}
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs text-slate-300 mt-2">
        <div className="bg-marine-900/60 p-2 rounded border border-slate-700/40">
          <span className="text-[10px] text-slate-400 block">Distance</span>
          <span className="font-bold text-white">{zone.distanceKm} km</span>
        </div>
        <div className="bg-marine-900/60 p-2 rounded border border-slate-700/40">
          <span className="text-[10px] text-slate-400 block">SST Gradient</span>
          <span className="font-bold text-white">{zone.seaSurfaceTemperature}°C</span>
        </div>
      </div>

      {zone.dominantSpecies && zone.dominantSpecies.length > 0 && (
        <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-1 truncate">
          <span className="text-emerald-400 font-medium">Species:</span>
          <span>{zone.dominantSpecies.join(", ")}</span>
        </div>
      )}
    </div>
  );
};
export default FishingZoneCard;
