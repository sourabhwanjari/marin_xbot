import React from "react";
import { ShieldAlert, AlertTriangle, Radio } from "lucide-react";
import { MarineAlert } from "@/types/marine";
import AlertCard from "./AlertCard";

interface AlertPanelProps {
  alerts: MarineAlert[];
}

export const AlertPanel: React.FC<AlertPanelProps> = ({ alerts }) => {
  const highCount = alerts.filter((a) => a.severity === "HIGH").length;

  return (
    <div className="bg-marine-900/90 backdrop-blur-md rounded-xl border border-cyan-500/20 p-4 shadow-marine-card mt-4">
      <div className="flex items-center justify-between mb-3 border-b border-slate-700/60 pb-2">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-5 h-5 text-amber-400 animate-pulse" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Active Marine Alerts & Navigational Warnings
          </h3>
        </div>
        <div className="flex items-center space-x-2">
          {highCount > 0 && (
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
              {highCount} High Priority
            </span>
          )}
          <span className="text-xs text-slate-400 font-mono">
            Source: INCOIS / IMD / Coast Guard (Simulated)
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {alerts.map((alert) => (
          <AlertCard key={alert.id} alert={alert} />
        ))}
      </div>
    </div>
  );
};
export default AlertPanel;
