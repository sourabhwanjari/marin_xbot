import React from "react";
import { ShieldAlert } from "lucide-react";
import { MarineAlert } from "@/types/marine";

interface SafetyCardProps {
  alerts: MarineAlert[];
}

export const SafetyCard: React.FC<SafetyCardProps> = ({ alerts }) => {
  const highAlerts = alerts.filter((a) => a.severity === "HIGH").length;
  const riskLevel = highAlerts > 0 ? "Elevated (Caution)" : "Moderate";

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm hover:shadow-md hover:border-slate-300 transition">
      <div className="flex items-center justify-between mb-2.5">
        <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-600" /> Maritime Safety
        </span>
        <span
          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
            highAlerts > 0
              ? "bg-amber-50 text-amber-700 border border-amber-200"
              : "bg-emerald-50 text-emerald-700 border border-emerald-200"
          }`}
        >
          {riskLevel}
        </span>
      </div>

      <div className="text-sm font-bold text-slate-900 mb-2">
        {alerts.length} Active Safety Bulletins
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs text-slate-700">
        <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
          <span className="text-[10px] text-slate-500 font-medium block">High Severity</span>
          <span className="font-bold text-rose-600">{highAlerts} Active</span>
        </div>
        <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
          <span className="text-[10px] text-slate-500 font-medium block">Safe Navigation</span>
          <span className="font-bold text-emerald-700">&lt; 15 NM Shore</span>
        </div>
      </div>

      <div className="mt-2.5 pt-2 border-t border-slate-100 text-[11px] text-slate-500 font-medium truncate">
        Primary advisory: Maintain engine vigilance during squalls.
      </div>
    </div>
  );
};

export default SafetyCard;
