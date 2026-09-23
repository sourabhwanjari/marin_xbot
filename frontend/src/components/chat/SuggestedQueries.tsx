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
      icon: <Compass className="w-3.5 h-3.5 text-emerald-600" />,
    },
    {
      text: "Is it safe to go fishing tomorrow morning near Mumbai?",
      icon: <Waves className="w-3.5 h-3.5 text-blue-600" />,
    },
    {
      text: "What are the sea conditions near me?",
      icon: <CloudSun className="w-3.5 h-3.5 text-sky-600" />,
    },
    {
      text: "Are there any cyclone or lightning alerts?",
      icon: <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />,
    },
  ];

  return (
    <div className="py-2">
      <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
        Suggested Inquiries
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
        {suggestions.map((item, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onSelectQuery(item.text)}
            className="flex items-center space-x-2 text-left bg-slate-50 hover:bg-slate-100 border border-slate-200 hover:border-slate-300 px-2.5 py-1.5 rounded-xl text-xs text-slate-700 hover:text-slate-900 transition disabled:opacity-50 disabled:cursor-not-allowed group cursor-pointer"
          >
            <span className="flex-shrink-0">{item.icon}</span>
            <span className="truncate group-hover:text-blue-700 transition font-medium">
              {item.text}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default SuggestedQueries;
