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
      icon: <Thermometer className="w-4 h-4 text-rose-500" />,
      highlight: true,
    },
    {
      label: "Chlorophyll-a",
      value: conditions.chlorophyll,
      subtext: "Phytoplankton Bloom",
      icon: <Droplets className="w-4 h-4 text-emerald-600" />,
      highlight: true,
    },
    {
      label: "Significant Wave Height",
      value: `${conditions.waveHeight} m`,
      subtext: "Moderate swell (9.5s period)",
      icon: <Waves className="w-4 h-4 text-blue-600" />,
    },
    {
      label: "Wind Speed & Direction",
      value: `${conditions.windSpeed} kts`,
      subtext: conditions.windDirection || "ENE (65°)",
      icon: <Wind className="w-4 h-4 text-sky-600" />,
    },
    {
      label: "Sea State Condition",
      value: conditions.seaState,
      subtext: "Beaufort Scale: Force 4",
      icon: <Compass className="w-4 h-4 text-amber-600" />,
    },
    {
      label: "Horizontal Visibility",
      value: `${conditions.visibility} NM`,
      subtext: "Clear navigational horizon",
      icon: <Eye className="w-4 h-4 text-teal-600" />,
    },
  ];

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600 border border-blue-100">
            <Waves className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            Oceanographic & Marine Conditions Telemetry
          </h3>
        </div>
        <span className="text-[11px] text-slate-500 font-mono font-medium">
          Updated: {conditions.updatedAt || "10:30 IST"}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {metrics.map((m, idx) => (
          <div
            key={idx}
            className="bg-slate-50 border border-slate-200/80 rounded-xl p-3.5 hover:bg-white hover:border-blue-300 hover:shadow-xs transition group"
          >
            <div className="flex items-center justify-between text-slate-500 mb-1.5">
              <span className="text-[11px] font-medium truncate">{m.label}</span>
              <span>{m.icon}</span>
            </div>
            <div className="text-lg font-black text-slate-900 group-hover:text-blue-700 transition">
              {m.value}
            </div>
            <div className="text-[11px] text-slate-500 truncate mt-0.5 font-medium">
              {m.subtext}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MarineConditionCard;
