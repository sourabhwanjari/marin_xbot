import React from "react";
import { AlertTriangle, ShieldAlert, Info } from "lucide-react";
import { MarineAlert } from "@/types/marine";

interface AlertCardProps {
  alert: MarineAlert;
}

export const AlertCard: React.FC<AlertCardProps> = ({ alert }) => {
  const getSeverityBadge = () => {
    switch (alert.severity) {
      case "HIGH":
        return {
          bg: "bg-rose-50 text-rose-700 border-rose-200",
          icon: <AlertTriangle className="w-4 h-4 text-rose-600" />,
          border: "border-l-rose-500",
        };
      case "MEDIUM":
        return {
          bg: "bg-amber-50 text-amber-700 border-amber-200",
          icon: <ShieldAlert className="w-4 h-4 text-amber-600" />,
          border: "border-l-amber-500",
        };
      case "LOW":
      default:
        return {
          bg: "bg-blue-50 text-blue-700 border-blue-200",
          icon: <Info className="w-4 h-4 text-blue-600" />,
          border: "border-l-blue-500",
        };
    }
  };

  const badge = getSeverityBadge();

  return (
    <div
      className={`bg-white border border-slate-200 border-l-4 ${badge.border} rounded-2xl p-4 hover:shadow-md hover:border-slate-300 transition shadow-xs`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center space-x-2">
          {badge.icon}
          <h4 className="text-xs sm:text-sm font-bold text-slate-900 leading-tight">
            {alert.type}
          </h4>
        </div>
        <span
          className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border ${badge.bg}`}
        >
          {alert.severity}
        </span>
      </div>

      <p className="text-xs text-slate-600 mb-2.5 font-normal leading-relaxed">
        {alert.short_description}
      </p>

      {alert.advisory && (
        <div className="text-[11px] text-amber-900 bg-amber-50/90 rounded-xl p-2 border border-amber-200/80 mb-2.5">
          <span className="font-bold text-amber-800">Advisory:</span> {alert.advisory}
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between text-[10px] text-slate-500 gap-1 border-t border-slate-100 pt-2 font-medium">
        <span className="truncate max-w-[200px]">
          📍 {alert.location}
        </span>
        <span className="font-mono text-blue-700 font-semibold">⏱ {alert.time}</span>
      </div>
    </div>
  );
};

export default AlertCard;
