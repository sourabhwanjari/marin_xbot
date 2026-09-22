import React from "react";
import { AlertTriangle, ShieldAlert, Waves, Zap, Anchor, Info } from "lucide-react";
import { MarineAlert } from "@/types/marine";

interface AlertCardProps {
  alert: MarineAlert;
}

export const AlertCard: React.FC<AlertCardProps> = ({ alert }) => {
  const getSeverityBadge = () => {
    switch (alert.severity) {
      case "HIGH":
        return {
          bg: "bg-rose-500/20 text-rose-300 border-rose-500/40",
          icon: <AlertTriangle className="w-4 h-4 text-rose-400" />,
          border: "border-l-rose-500",
        };
      case "MEDIUM":
        return {
          bg: "bg-amber-500/20 text-amber-300 border-amber-500/40",
          icon: <ShieldAlert className="w-4 h-4 text-amber-400" />,
          border: "border-l-amber-500",
        };
      case "LOW":
      default:
        return {
          bg: "bg-blue-500/20 text-blue-300 border-blue-500/40",
          icon: <Info className="w-4 h-4 text-blue-400" />,
          border: "border-l-blue-500",
        };
    }
  };

  const badge = getSeverityBadge();

  return (
    <div
      className={`bg-marine-850/80 border border-slate-700/60 border-l-4 ${badge.border} rounded-lg p-3 hover:border-cyan-500/40 transition shadow-sm`}
    >
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div className="flex items-center space-x-2">
          {badge.icon}
          <h4 className="text-xs sm:text-sm font-bold text-white leading-tight">
            {alert.type}
          </h4>
        </div>
        <span
          className={`text-[10px] uppercase font-extrabold tracking-wider px-2 py-0.5 rounded border ${badge.bg}`}
        >
          {alert.severity}
        </span>
      </div>

      <p className="text-xs text-slate-200 mb-2 font-normal">
        {alert.short_description}
      </p>

      {alert.advisory && (
        <div className="text-[11px] text-amber-300/90 bg-marine-900/60 rounded p-1.5 border border-slate-700/40 mb-2">
          <span className="font-semibold text-amber-400">Advisory:</span> {alert.advisory}
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between text-[10px] text-slate-400 gap-1 border-t border-slate-700/40 pt-1.5">
        <span className="truncate max-w-[200px] font-medium text-slate-300">
          📍 {alert.location}
        </span>
        <span className="font-mono text-cyan-400/80">⏱ {alert.time}</span>
      </div>
    </div>
  );
};
export default AlertCard;
