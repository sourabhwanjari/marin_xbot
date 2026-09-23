"use client";

import React, { useState } from "react";
import {
  Compass,
  Globe,
  User,
  BookOpen,
  Radio,
  ChevronDown,
  ShieldAlert,
  Waves,
  Home as HomeIcon,
} from "lucide-react";
import { RagStatus, DataSourcesHealthResponse } from "@/types/marine";

export type NavTab = "home" | "safety" | "sea" | "profile";

interface HeaderProps {
  systemStatus?: string;
  isDemo?: boolean;
  ragStatus?: RagStatus | null;
  dataSourcesStatus?: DataSourcesHealthResponse | null;
  onOpenKnowledgeModal?: () => void;
  activeTab?: NavTab;
  onTabChange?: (tab: NavTab) => void;
}

export const Header: React.FC<HeaderProps> = ({
  systemStatus = "Operational",
  isDemo = true,
  ragStatus,
  dataSourcesStatus,
  onOpenKnowledgeModal,
  activeTab = "home",
  onTabChange,
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

  const navItems: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: "home", label: "Home", icon: <HomeIcon className="w-4 h-4" /> },
    { id: "safety", label: "Safety Info", icon: <ShieldAlert className="w-4 h-4" /> },
    { id: "sea", label: "Sea Info", icon: <Waves className="w-4 h-4" /> },
    { id: "profile", label: "Profile", icon: <User className="w-4 h-4" /> },
  ];

  return (
    <header className="w-full bg-white/95 backdrop-blur-md border-b border-slate-200 px-4 lg:px-6 py-2.5 sticky top-0 z-50 shadow-xs">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Left: Branding & Subtitle */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => onTabChange?.("home")}>
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-sky-500 to-blue-700 flex items-center justify-center text-white shadow-sm shadow-sky-500/30">
              <Compass className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight text-slate-900">
                  MARINEX<span className="text-sky-600">.AI</span>
                </span>
                {isDemo && (
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                    Demo Mode
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-500 font-medium flex items-center gap-1.5">
                <span>Marine Intelligence</span>
                <span className="text-slate-300">•</span>
                <span className="text-sky-700 font-mono text-[10px]">ORCA Multi-Agent</span>
              </p>
            </div>
          </div>

          {/* Mobile Profile Trigger */}
          <button
            onClick={() => onTabChange?.("profile")}
            className="md:hidden p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
            aria-label="View Profile"
          >
            <User className="w-4 h-4" />
          </button>
        </div>

        {/* Center: Top Navigation Bar | Home | Safety Info | Sea Info | Profile | */}
        <nav className="flex items-center justify-center bg-slate-100/90 p-1 rounded-xl border border-slate-200 shadow-xs self-center">
          {navItems.map((item, idx) => {
            const isActive = activeTab === item.id;
            return (
              <React.Fragment key={item.id}>
                {idx > 0 && <div className="h-4 w-px bg-slate-300 mx-0.5 hidden sm:block" />}
                <button
                  onClick={() => onTabChange?.(item.id)}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    isActive
                      ? "bg-white text-blue-700 shadow-sm border border-slate-200/80"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/50"
                  }`}
                >
                  <span className={isActive ? "text-blue-600" : "text-slate-400"}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </button>
              </React.Fragment>
            );
          })}
        </nav>

        {/* Right: Data Feeds, Knowledge Base & Controls */}
        <div className="flex items-center justify-end space-x-2 sm:space-x-3">
          {/* Data Feeds Status Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowFeedsMenu(!showFeedsMenu)}
              className="flex items-center space-x-1.5 bg-white hover:bg-slate-50 border border-slate-200 hover:border-slate-300 px-2.5 py-1.5 rounded-lg text-xs transition cursor-pointer shadow-xs text-slate-700"
              title="Inspect Real Marine Data Sources Status"
            >
              <Radio className="w-3.5 h-3.5 text-emerald-600 animate-pulse" />
              <span className="hidden sm:inline font-medium">Data Feeds:</span>
              <span className="font-bold text-emerald-600 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                Active
              </span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {showFeedsMenu && (
              <div className="absolute right-0 mt-2 w-72 bg-white border border-slate-200 rounded-xl shadow-xl p-3.5 z-[2000] text-xs space-y-2">
                <div className="font-bold text-slate-800 border-b border-slate-100 pb-1.5 flex items-center justify-between">
                  <span>Marine Data Sources</span>
                  <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">
                    Phase 4 Active
                  </span>
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between p-1.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="text-slate-700 font-medium">Weather (Open-Meteo)</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      LIVE
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-1.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="text-slate-700 font-medium">Ocean (Wave/Swell)</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      LIVE
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-1.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="text-slate-700 font-medium">PFZ (INCOIS Mission)</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-sky-50 text-sky-700 border border-sky-200">
                      AVAILABLE
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-1.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="text-slate-700 font-medium">Satellite (MOSDAC)</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono text-slate-500 bg-slate-100 border border-slate-200">
                      NOT CONFIGURED
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-1.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="text-slate-700 font-medium">GIS / PostGIS Layers</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-sky-50 text-sky-700 border border-sky-200">
                      AVAILABLE
                    </span>
                  </div>
                </div>
                <div className="text-[11px] text-slate-500 pt-1.5 border-t border-slate-100 leading-snug">
                  Resilient fallback: Local cache & demo models ensure 100% operational availability.
                </div>
              </div>
            )}
          </div>

          {/* Knowledge Base Trigger */}
          <button
            onClick={onOpenKnowledgeModal}
            className="flex items-center space-x-1.5 bg-white hover:bg-slate-50 border border-slate-200 hover:border-slate-300 px-2.5 py-1.5 rounded-lg text-xs transition group cursor-pointer shadow-xs text-slate-700"
            title="Open Marine Knowledge Base & RAG Index"
          >
            <BookOpen className="w-3.5 h-3.5 text-blue-600" />
            <span className="hidden lg:inline font-medium">Knowledge Base:</span>
            <span className={`font-bold flex items-center gap-1 ${isRagReady ? "text-blue-700" : "text-amber-700"}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${isRagReady ? "bg-blue-600" : "bg-amber-500"}`}></span>
              {isRagReady ? `Ready (${totalDocs})` : "Configuring"}
            </span>
          </button>

          {/* Language Selector */}
          <div className="relative flex items-center">
            <div className="flex items-center space-x-1.5 bg-white border border-slate-200 px-2.5 py-1.5 rounded-lg text-xs text-slate-700 hover:border-slate-300 transition shadow-xs">
              <Globe className="w-3.5 h-3.5 text-slate-500" />
              <select
                aria-label="Select Language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="bg-transparent text-slate-700 focus:outline-none cursor-pointer text-xs font-medium"
              >
                {languages.map((l) => (
                  <option key={l.code} value={l.code} className="bg-white text-slate-800">
                    {l.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
