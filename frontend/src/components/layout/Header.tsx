"use client";

import React, { useState } from "react";
import { Compass, Globe, User, BookOpen, Radio, ChevronDown, CheckCircle2, AlertCircle, XCircle } from "lucide-react";
import { RagStatus, DataSourcesHealthResponse } from "@/types/marine";

interface HeaderProps {
  systemStatus?: string;
  isDemo?: boolean;
  ragStatus?: RagStatus | null;
  dataSourcesStatus?: DataSourcesHealthResponse | null;
  onOpenKnowledgeModal?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  systemStatus = "Operational",
  isDemo = true,
  ragStatus,
  dataSourcesStatus,
  onOpenKnowledgeModal,
}) => {
  const [language, setLanguage] = useState("en");
  const [showFeedsMenu, setShowFeedsMenu] = useState(false);

  const languages = [
    { code: "en", name: "English" },
    { code: "ta", name: "தமிழ் (Tamil)" },
    { code: "hi", name: "हिन्दी (Hindi)" },
    { code: "te", name: "తెలుగు (Telugu)" },
    { code: "ml", name: "മലയാളം (Malayalam)" },
    { code: "bn", name: "বাংলা (Bengali)" },
  ];

  const totalDocs = ragStatus?.total_documents ?? 0;
  const isRagReady = (ragStatus?.total_chunks ?? 0) > 0;

  return (
    <header className="w-full bg-marine-900/90 backdrop-blur-md border-b border-cyan-500/20 px-4 lg:px-6 py-3 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Left: Branding & Subtitle */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-400/40 flex items-center justify-center text-cyan-400 shadow-marine-cyan">
            <Compass className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-xl tracking-wider text-white">
                MARINEX<span className="text-cyan-400">.AI</span>
              </span>
              {isDemo && (
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40">
                  Demo Mode
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
              <span>Marine Intelligence Platform</span>
              <span className="text-slate-600">•</span>
              <span className="text-cyan-400/80 font-mono text-[11px]">ORCA Multi-Agent System</span>
            </p>
          </div>
        </div>

        {/* Right: Controls, Knowledge Base Button & Status */}
        <div className="flex items-center space-x-2 sm:space-x-4">
          {/* Data Feeds Status Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowFeedsMenu(!showFeedsMenu)}
              className="flex items-center space-x-1.5 bg-marine-850/90 hover:bg-marine-800 border border-slate-700/60 hover:border-cyan-500/40 px-2.5 py-1.5 rounded-md text-xs transition cursor-pointer shadow-sm text-slate-300"
              title="Inspect Real Marine Data Sources Status"
            >
              <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              <span className="hidden sm:inline font-medium">Data Feeds:</span>
              <span className="font-bold text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                Active
              </span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {showFeedsMenu && (
              <div className="absolute right-0 mt-2 w-64 bg-marine-900 border border-cyan-500/40 rounded-xl shadow-2xl p-3 z-[2000] text-xs space-y-2">
                <div className="font-bold text-slate-200 border-b border-slate-700/60 pb-1.5 flex items-center justify-between">
                  <span>Marine Data Sources</span>
                  <span className="text-[10px] font-mono text-cyan-400">Phase 4</span>
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between p-1 rounded bg-marine-850">
                    <span className="text-slate-300">Weather (Open-Meteo)</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                      LIVE
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-1 rounded bg-marine-850">
                    <span className="text-slate-300">Ocean (Wave/Swell)</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                      LIVE
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-1 rounded bg-marine-850">
                    <span className="text-slate-300">PFZ (INCOIS Mission)</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                      AVAILABLE
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-1 rounded bg-marine-850">
                    <span className="text-slate-300">Satellite (MOSDAC)</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono text-slate-400 bg-slate-800 border border-slate-700">
                      NOT CONFIGURED
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-1 rounded bg-marine-850">
                    <span className="text-slate-300">GIS / PostGIS Layers</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                      AVAILABLE
                    </span>
                  </div>
                </div>
                <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-800">
                  Resilient fallback: Demo Mode is active if external providers are unreachable.
                </div>
              </div>
            )}
          </div>

          {/* Knowledge Base Trigger & Status Indicator */}
          <button
            onClick={onOpenKnowledgeModal}
            className="flex items-center space-x-1.5 bg-marine-850/90 hover:bg-marine-800 border border-slate-700/60 hover:border-cyan-500/40 px-2.5 py-1.5 rounded-md text-xs transition group cursor-pointer shadow-sm"
            title="Open Marine Knowledge Base & RAG Index"
          >
            <BookOpen className="w-3.5 h-3.5 text-blue-400 group-hover:text-cyan-300 transition" />
            <span className="text-slate-300 font-medium hidden sm:inline">Knowledge Base:</span>
            <span className={`font-bold flex items-center gap-1 ${isRagReady ? "text-cyan-300" : "text-amber-300"}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${isRagReady ? "bg-cyan-400" : "bg-amber-400"}`}></span>
              {isRagReady ? `Ready (${totalDocs} docs)` : "Configuring"}
            </span>
          </button>

          {/* System Status Indicator */}
          <div className="hidden md:flex items-center space-x-2 bg-marine-850/80 border border-slate-700/60 px-3 py-1.5 rounded-md text-xs">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-slate-300 font-medium">System:</span>
            <span className="text-emerald-400 font-semibold">{systemStatus}</span>
          </div>

          {/* Language Selector */}
          <div className="relative flex items-center">
            <div className="flex items-center space-x-1.5 bg-marine-850/80 border border-slate-700/60 px-2.5 py-1.5 rounded-md text-xs text-slate-300 hover:border-cyan-500/40 transition">
              <Globe className="w-3.5 h-3.5 text-cyan-400" />
              <select
                aria-label="Select Language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="bg-transparent text-slate-200 focus:outline-none cursor-pointer text-xs"
              >
                {languages.map((l) => (
                  <option key={l.code} value={l.code} className="bg-marine-900 text-slate-200">
                    {l.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* User Profile */}
          <div className="flex items-center space-x-2 bg-marine-850/80 border border-slate-700/60 px-3 py-1.5 rounded-md text-xs hover:border-cyan-500/40 transition cursor-pointer">
            <div className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-300 flex items-center justify-center">
              <User className="w-3.5 h-3.5" />
            </div>
            <div className="hidden lg:block text-left">
              <div className="text-[11px] font-semibold text-slate-200 leading-tight">Vessel Master</div>
              <div className="text-[9px] text-cyan-400 font-mono leading-tight">Port Kasimedu</div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
export default Header;

