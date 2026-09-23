import React from "react";
import { ShieldAlert } from "lucide-react";
import { MarineAlert } from "@/types/marine";
import AlertCard from "./AlertCard";

interface AlertPanelProps {
  alerts: MarineAlert[];
}

export const AlertPanel: React.FC<AlertPanelProps> = ({ alerts }) => {
  const highCount = alerts.filter((a) => a.severity === "HIGH").length;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 rounded-lg bg-amber-50 text-amber-600 border border-amber-100">
            <ShieldAlert className="w-4 h-4 animate-pulse" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            Active Marine Alerts & Navigational Warnings
          </h3>
        </div>
        <div className="flex items-center space-x-2">
          {highCount > 0 && (
            <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 animate-pulse">
              {highCount} High Priority
            </span>
          )}
          <span className="text-xs text-slate-500 font-medium hidden sm:inline">
            Source: INCOIS / IMD / Coast Guard
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {alerts.map((alert) => (
          <AlertCard key={alert.id} alert={alert} />
        ))}
      </div>
    </div>
  );
};

export default AlertPanel;
