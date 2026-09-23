import React from "react";

export const MapLegend: React.FC = () => {
  return (
    <div className="absolute bottom-4 right-4 z-[1000] bg-white/95 backdrop-blur-md border border-slate-200 rounded-xl p-3 text-xs text-slate-700 shadow-lg select-none">
      <div className="font-bold text-[11px] uppercase tracking-wider text-slate-900 mb-2 border-b border-slate-100 pb-1">
        Marine GIS Legend
      </div>
      <div className="space-y-1.5 font-medium">
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-emerald-500 flex-shrink-0 shadow-xs"></span>
          <span>🟢 Favorable Fishing Zone</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-amber-400 flex-shrink-0 shadow-xs"></span>
          <span>🟡 Caution Area</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-rose-500 flex-shrink-0 shadow-xs"></span>
          <span>🔴 Marine Hazard</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-blue-600 flex-shrink-0 shadow-xs"></span>
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
