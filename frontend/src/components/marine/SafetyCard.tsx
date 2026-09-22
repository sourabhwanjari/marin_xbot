import React from "react";
import { ShieldAlert, AlertTriangle, ShieldCheck } from "lucide-react";
import { MarineAlert } from "@/types/marine";

interface SafetyCardProps {
  alerts: MarineAlert[];
}

export const SafetyCard: React.FC<SafetyCardProps> = ({ alerts }) => {
  const highAlerts = alerts.filter((a) => a.severity === "HIGH").length;
  const riskLevel = highAlerts > 0 ? "Elevated (Caution)" : "Moderate";

  return (
    <div className="bg-marine-850/80 border border-slate-700/60 rounded-xl p-3.5 hover:border-amber-500/40 transition">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400" /> Maritime Safety
        </span>
        <span
          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
            highAlerts > 0
              ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
              : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
          }`}
        >
          {riskLevel}
        </span>
      </div>

      <div className="text-sm font-bold text-white mb-1">
        {alerts.length} Active Safety Bulletins
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs text-slate-300 mt-2">
        <div className="bg-marine-900/60 p-2 rounded border border-slate-700/40">
          <span className="text-[10px] text-slate-400 block">High Severity</span>
          <span className="font-bold text-rose-400">{highAlerts} Active</span>
        </div>
        <div className="bg-marine-900/60 p-2 rounded border border-slate-700/40">
          <span className="text-[10px] text-slate-400 block">Safe Corridor</span>
          <span className="font-bold text-emerald-400">&lt; 15 NM Shore</span>
        </div>
      </div>

      <div className="mt-2 text-[11px] text-slate-400 truncate">
        Primary advisory: Avoid offshore deep trench swells.
      </div>
    </div>
  );
};
export default SafetyCard;
