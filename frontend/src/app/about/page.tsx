"use client";

import React from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import {
  Compass,
  Workflow,
  Cpu,
  Waves,
  ShieldCheck,
  Radio,
  ArrowRight,
} from "lucide-react";

export default function AboutPage() {
  const agentPillars = [
    {
      title: "Planner & Query Router",
      desc: "Deconstructs natural language marine inquiries into geographical coordinates, temporal horizons, and agent execution plans.",
      icon: <Workflow className="w-5 h-5 text-cyan-400" />,
    },
    {
      title: "Meteorological Agent",
      desc: "Analyzes surface wind squalls, gusts, barometric pressure changes, and precipitation via IMD and Open-Meteo feeds.",
      icon: <Radio className="w-5 h-5 text-sky-400" />,
    },
    {
      title: "Oceanographic Agent",
      desc: "Monitors significant wave heights, swell periods, current velocity, and sea-surface temperatures (SST) via INCOIS telemetry.",
      icon: <Waves className="w-5 h-5 text-blue-400" />,
    },
    {
      title: "Geospatial & PFZ Agent",
      desc: "Maps Potential Fishing Zones, maritime boundaries, port approaches, and restricted marine conservation zones.",
      icon: <Compass className="w-5 h-5 text-teal-400" />,
    },
    {
      title: "Risk Reasoning Engine",
      desc: "Aggregates multi-agent telemetry and evaluates voyage hazards against Beaufort wind limits and vessel safety thresholds.",
      icon: <ShieldCheck className="w-5 h-5 text-emerald-400" />,
    },
    {
      title: "Response Synthesizer",
      desc: "Translates complex oceanographic calculations into actionable, natural-language advisories tailored for coastal fishermen.",
      icon: <Cpu className="w-5 h-5 text-indigo-400" />,
    },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-[#070d19] text-slate-100">
      {/* Top Navigation Bar */}
      <Header />

      {/* Main Content Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8 sm:py-12 space-y-10">
        {/* Hero Section */}
        <section className="text-center space-y-4 max-w-2xl mx-auto">
          <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br from-cyan-500 via-sky-600 to-blue-700 mx-auto flex items-center justify-center text-white shadow-xl shadow-cyan-500/25 border border-cyan-400/30">
            <Compass className="w-8 h-8 sm:w-9 sm:h-9" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            About <span className="text-cyan-400">MARINEX AI</span>
          </h1>
          <p className="text-sm sm:text-base text-cyan-300/90 font-medium">
            ORCA: Marine EcOsystem Reasoning with Collaborative Agents
          </p>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            MARINEX AI is an autonomous, multi-agent marine intelligence system engineered to deliver real-time oceanographic reasoning, Potential Fishing Zone (PFZ) guidance, and voyage safety assessments to fishermen and coastal maritime operators.
          </p>
        </section>

        {/* Multi-Agent Architecture */}
        <section className="space-y-4">
          <div className="border-b border-slate-800 pb-2">
            <h2 className="text-lg sm:text-xl font-bold text-white flex items-center gap-2">
              <Workflow className="w-5 h-5 text-cyan-400" />
              <span>LangGraph Multi-Agent Architecture</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Every user query is collaboratively resolved by dedicated domain agents operating over shared state.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agentPillars.map((agent, idx) => (
              <div
                key={idx}
                className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-4 sm:p-5 shadow-lg space-y-2 hover:border-slate-700 transition"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-2 rounded-xl bg-slate-950 border border-slate-800">
                    {agent.icon}
                  </div>
                  <h3 className="font-bold text-sm text-white">{agent.title}</h3>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed pt-1">
                  {agent.desc}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Phase 5A Marine Data Gateway */}
        <section className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-4 shadow-xl">
          <h2 className="text-lg sm:text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <span>Phase 5A: Marine Data Gateway</span>
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            The Marine Data Gateway provides an authoritative, provider-agnostic data foundation. It bridges the multi-agent reasoning graph with national marine agencies—including the <strong>India Meteorological Department (IMD)</strong>, <strong>Indian National Centre for Ocean Information Services (INCOIS)</strong>, and <strong>MOSDAC ISRO</strong>—with strict zero-hallucination guardrails and resilient Open-Meteo fallback capabilities.
          </p>

          <div className="pt-2">
            <Link
              href="/"
              className="inline-flex items-center gap-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-4 py-2 rounded-xl text-xs sm:text-sm shadow-md shadow-cyan-500/25 transition cursor-pointer"
            >
              <span>Start Marine Conversation</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </section>

        {/* Operational Safety Disclaimer */}
        <footer className="text-center pt-4 pb-6 text-xs text-slate-500 max-w-xl mx-auto space-y-1">
          <p>
            MARINEX AI is an assistive decision-support system. Always verify voyage safety with official Indian Coast Guard and IMD bulletins before sailing.
          </p>
          <p className="text-[11px] font-mono text-slate-600">
            MARINEX AI 5.0 • ORCA Multi-Agent Framework
          </p>
        </footer>
      </main>
    </div>
  );
}
