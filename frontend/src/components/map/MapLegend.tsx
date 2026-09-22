import React from "react";

export const MapLegend: React.FC = () => {
  return (
    <div className="absolute bottom-4 right-4 z-[1000] bg-marine-900/90 backdrop-blur-md border border-slate-700/80 rounded-lg p-2.5 text-xs text-slate-200 shadow-marine-card select-none">
      <div className="font-bold text-[11px] uppercase tracking-wider text-cyan-400 mb-2 border-b border-slate-700/50 pb-1">
        Marine GIS Legend
      </div>
      <div className="space-y-1.5 font-medium">
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.7)] flex-shrink-0"></span>
          <span>🟢 Favorable Fishing Zone</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.7)] flex-shrink-0"></span>
          <span>🟡 Caution Area</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(239,68,68,0.7)] flex-shrink-0"></span>
          <span>🔴 Marine Hazard</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(56,189,248,0.8)] flex-shrink-0"></span>
          <span>🔵 User Location</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-slate-700 border border-slate-500 flex-shrink-0"></span>
          <span>⚫ Restricted Zone</span>
        </div>
      </div>
    </div>
  );
};
export default MapLegend;
