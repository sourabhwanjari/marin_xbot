import React from "react";
import { Compass, Waves, CloudSun, AlertTriangle } from "lucide-react";

interface SuggestedQueriesProps {
  onSelectQuery: (query: string) => void;
  disabled?: boolean;
}

export const SuggestedQueries: React.FC<SuggestedQueriesProps> = ({
  onSelectQuery,
  disabled = false,
}) => {
  const suggestions = [
    {
      text: "Where is the nearest Potential Fishing Zone?",
      icon: <Compass className="w-3.5 h-3.5 text-emerald-400" />,
    },
    {
      text: "Is it safe to go fishing tomorrow morning near Mumbai?",
      icon: <Waves className="w-3.5 h-3.5 text-cyan-400" />,
    },
    {
      text: "What are the sea conditions near me?",
      icon: <CloudSun className="w-3.5 h-3.5 text-blue-400" />,
    },
    {
      text: "Are there any cyclone or lightning alerts?",
      icon: <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />,
    },
  ];

  return (
    <div className="py-2">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
        Suggested Inquiries
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
        {suggestions.map((item, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onSelectQuery(item.text)}
            className="flex items-center space-x-2 text-left bg-marine-850/70 hover:bg-marine-800/90 border border-slate-700/60 hover:border-cyan-500/40 px-2.5 py-1.5 rounded-lg text-xs text-slate-300 hover:text-white transition disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <span className="flex-shrink-0">{item.icon}</span>
            <span className="truncate group-hover:text-cyan-300 transition">
              {item.text}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};
export default SuggestedQueries;
