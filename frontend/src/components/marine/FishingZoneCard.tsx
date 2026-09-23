import React from "react";
import { Fish } from "lucide-react";
import { FishingZone } from "@/types/marine";

interface FishingZoneCardProps {
  zone: FishingZone;
}

export const FishingZoneCard: React.FC<FishingZoneCardProps> = ({ zone }) => {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm hover:shadow-md hover:border-slate-300 transition">
      <div className="flex items-center justify-between mb-2.5">
        <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <Fish className="w-3.5 h-3.5 text-emerald-600" /> Fishing Intelligence
        </span>
        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
          {zone.suitability}
        </span>
      </div>

      <div className="text-sm font-bold text-slate-900 truncate mb-2">
        {zone.name}
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs text-slate-700">
        <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
          <span className="text-[10px] text-slate-500 font-medium block">Distance</span>
          <span className="font-bold text-slate-900">{zone.distanceKm} km</span>
        </div>
        <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
          <span className="text-[10px] text-slate-500 font-medium block">SST Gradient</span>
          <span className="font-bold text-slate-900">{zone.seaSurfaceTemperature}°C</span>
        </div>
      </div>

      {zone.dominantSpecies && zone.dominantSpecies.length > 0 && (
        <div className="mt-2.5 pt-2 border-t border-slate-100 text-[11px] text-slate-500 flex items-center gap-1 truncate">
          <span className="text-emerald-700 font-semibold">Target Species:</span>
          <span>{zone.dominantSpecies.join(", ")}</span>
        </div>
      )}
    </div>
  );
};

export default FishingZoneCard;
