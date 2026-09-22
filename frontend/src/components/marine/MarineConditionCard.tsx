import React from "react";
import { Thermometer, Wind, Eye, Waves, Droplets, Compass } from "lucide-react";
import { MarineConditions } from "@/types/marine";

interface MarineConditionCardProps {
  conditions: MarineConditions;
}

export const MarineConditionCard: React.FC<MarineConditionCardProps> = ({ conditions }) => {
  const metrics = [
    {
      label: "Sea Surface Temp (SST)",
      value: `${conditions.seaSurfaceTemperature}°C`,
      subtext: "Thermal Front Detected",
      icon: <Thermometer className="w-4 h-4 text-rose-400" />,
      highlight: true,
    },
    {
      label: "Chlorophyll-a",
      value: conditions.chlorophyll,
      subtext: "Phytoplankton Bloom",
      icon: <Droplets className="w-4 h-4 text-emerald-400" />,
      highlight: true,
    },
    {
      label: "Significant Wave Height",
      value: `${conditions.waveHeight} m`,
      subtext: "Moderate swell (9.5s period)",
      icon: <Waves className="w-4 h-4 text-cyan-400" />,
    },
    {
      label: "Wind Speed & Direction",
      value: `${conditions.windSpeed} kts`,
      subtext: conditions.windDirection || "ENE (65°)",
      icon: <Wind className="w-4 h-4 text-blue-400" />,
    },
    {
      label: "Sea State Condition",
      value: conditions.seaState,
      subtext: "Beaufort Scale: Force 4",
      icon: <Compass className="w-4 h-4 text-amber-400" />,
    },
    {
      label: "Horizontal Visibility",
      value: `${conditions.visibility} NM`,
      subtext: "Clear navigational horizon",
      icon: <Eye className="w-4 h-4 text-teal-400" />,
    },
  ];

  return (
    <div className="bg-marine-900/90 backdrop-blur-md rounded-xl border border-cyan-500/20 p-4 shadow-marine-card">
      <div className="flex items-center justify-between mb-3 border-b border-slate-700/60 pb-2">
        <div className="flex items-center space-x-2">
          <Waves className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Oceanographic & Marine Conditions
          </h3>
        </div>
        <span className="text-[11px] text-slate-400 font-mono">
          Updated: {conditions.updatedAt || "10:30 IST"}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {metrics.map((m, idx) => (
          <div
            key={idx}
            className="bg-marine-850/80 border border-slate-700/60 rounded-lg p-3 hover:border-cyan-500/40 transition group"
          >
            <div className="flex items-center justify-between text-slate-400 mb-1.5">
              <span className="text-[11px] font-medium truncate">{m.label}</span>
              <span>{m.icon}</span>
            </div>
            <div className="text-base font-extrabold text-white group-hover:text-cyan-300 transition">
              {m.value}
            </div>
            <div className="text-[10px] text-slate-400 truncate mt-0.5">
              {m.subtext}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
export default MarineConditionCard;
