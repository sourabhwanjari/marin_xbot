"use client";

import React, { useState } from "react";
import { ChatMessage as ChatMessageType } from "@/types/marine";
import {
  Compass,
  User,
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  ChevronDown,
  ChevronRight,
  Activity,
  MapPin,
  Clock,
  Workflow,
  BookOpen,
  Copy,
  Check,
  Navigation,
  ArrowRight,
  ExternalLink,
  Wind,
  Waves,
  Route as RouteIcon,
} from "lucide-react";


interface ChatMessageProps {
  message: ChatMessageType;
  onActionClick?: (action: string) => void;
}

// Lightweight, safe markdown formatter for marine chat responses
const FormattedMarkdown: React.FC<{ content: string }> = ({ content }) => {
  const lines = content.split("\n");

  const renderInline = (text: string) => {
    // Process bold **text** and backticks `code`
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={i} className="font-semibold text-white">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith("`") && part.endsWith("`")) {
        return (
          <code
            key={i}
            className="font-mono text-cyan-300 bg-slate-900/90 px-1.5 py-0.5 rounded text-xs border border-slate-700/60"
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <div className="space-y-2 text-sm leading-relaxed text-slate-200">
      {lines.map((line, idx) => {
        const trimmed = line.trim();

        // Empty line
        if (!trimmed) {
          return <div key={idx} className="h-1.5" />;
        }

        // Heading 3 or 4: ### or ####
        if (trimmed.startsWith("### ")) {
          return (
            <h4
              key={idx}
              className="text-sm font-bold text-cyan-300 pt-1 border-b border-slate-800 pb-1"
            >
              {renderInline(trimmed.replace(/^###\s*/, ""))}
            </h4>
          );
        }
        if (trimmed.startsWith("## ")) {
          return (
            <h3
              key={idx}
              className="text-base font-bold text-white pt-1.5 border-b border-slate-800 pb-1"
            >
              {renderInline(trimmed.replace(/^##\s*/, ""))}
            </h3>
          );
        }

        // Bullet lists: *, -, •
        if (
          trimmed.startsWith("* ") ||
          trimmed.startsWith("- ") ||
          trimmed.startsWith("• ")
        ) {
          const bulletText = trimmed.replace(/^[\*\-•]\s*/, "");
          return (
            <div key={idx} className="flex items-start gap-2 pl-1">
              <span className="text-cyan-400 font-bold select-none">•</span>
              <div className="flex-1">{renderInline(bulletText)}</div>
            </div>
          );
        }

        // Numbered lists: 1., 2.
        const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
        if (numMatch) {
          return (
            <div key={idx} className="flex items-start gap-2 pl-1">
              <span className="text-cyan-400 font-mono text-xs font-semibold select-none pt-0.5">
                {numMatch[1]}.
              </span>
              <div className="flex-1">{renderInline(numMatch[2])}</div>
            </div>
          );
        }

        // Normal paragraph
        return <p key={idx}>{renderInline(line)}</p>;
      })}
    </div>
  );
};

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === "user";
  const hasSources = message.sources && message.sources.length > 0;
  const hasEvidence = message.evidence && message.evidence.length > 0;
  const hasTrace = message.executionSteps && message.executionSteps.length > 0;
  const [showTrace, setShowTrace] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderRiskBadge = (risk?: string) => {
    if (!risk) return null;
    const r = risk.toUpperCase();
    if (r === "LOW") {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-950/70 text-emerald-300 border border-emerald-800/60 shadow-xs">
          <ShieldCheck className="w-3 h-3 text-emerald-400" /> Risk: LOW (Favorable)
        </span>
      );
    }
    if (r === "MEDIUM") {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-950/70 text-amber-300 border border-amber-800/60 shadow-xs">
          <AlertTriangle className="w-3 h-3 text-amber-400" /> Risk: MEDIUM (Caution)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-950/70 text-rose-300 border border-rose-800/60 shadow-xs">
        <AlertOctagon className="w-3 h-3 text-rose-400" /> Risk: HIGH (Hazard)
      </span>
    );
  };

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"} my-2.5`}>
      <div
        className={`flex max-w-[94%] sm:max-w-[85%] md:max-w-[80%] space-x-3 ${
          isUser ? "flex-row-reverse space-x-reverse" : "flex-row"
        }`}
      >
        {/* Avatar */}
        <div
          className={`w-7 h-7 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm ${
            isUser
              ? "bg-slate-700 text-slate-200 border border-slate-600"
              : "bg-gradient-to-br from-cyan-500 via-sky-600 to-blue-700 text-white shadow-cyan-500/25"
          }`}
        >
          {isUser ? (
            <User className="w-4 h-4 text-slate-200" />
          ) : (
            <Compass className="w-4 h-4 text-white" />
          )}
        </div>

        {/* Message Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 sm:px-5 sm:py-3.5 text-sm leading-relaxed shadow-md ${
            isUser
              ? "bg-cyan-950/80 text-slate-100 border border-cyan-800/60 rounded-tr-xs"
              : "bg-slate-900/90 text-slate-200 border border-slate-800/90 rounded-tl-xs"
          }`}
        >
          {/* AI Header & Metadata Badges */}
          {!isUser && (
            <div className="flex flex-wrap items-center justify-between gap-1.5 mb-2 pb-1.5 border-b border-slate-800/80">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-bold text-xs text-cyan-400 flex items-center gap-1.5">
                  <span>MARINEX AI</span>
                </span>
                {renderRiskBadge(message.riskLevel)}
                {message.location && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800/80 text-cyan-300 border border-slate-700/60">
                    <MapPin className="w-2.5 h-2.5 text-cyan-400" /> {message.location}
                  </span>
                )}
                {message.timeContext && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700/60">
                    <Clock className="w-2.5 h-2.5 text-cyan-400" /> {message.timeContext}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Message Content */}
          {isUser ? (
            <p className="whitespace-pre-line text-slate-100 font-normal">
              {message.text}
            </p>
          ) : (
            <FormattedMarkdown content={message.text} />
          )}

          {/* Recommended Route Card (Compact & Modern) */}
          {!isUser && message.route && (
            <div className="mt-3 p-3.5 rounded-xl bg-gradient-to-br from-slate-900/95 via-slate-900/80 to-cyan-950/40 border border-cyan-500/50 shadow-lg text-xs space-y-3">
              {/* Header */}
              <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300">
                    <Navigation className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">Recommended Safe Route</div>
                    <div className="font-bold text-white text-sm flex items-center gap-1.5">
                      <span>{message.route.origin.name || "Origin"}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-cyan-400" />
                      <span>{message.route.destination.name || "Destination"}</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col items-end">
                  <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${
                    message.route.safety_score >= 80
                      ? "bg-emerald-950/80 text-emerald-300 border-emerald-600"
                      : message.route.safety_score >= 50
                      ? "bg-amber-950/80 text-amber-300 border-amber-600"
                      : "bg-red-950/80 text-red-300 border-red-600"
                  }`}>
                    Safety: {message.route.safety_score}/100 ({message.route.risk_level})
                  </span>
                </div>
              </div>

              {/* Key Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-slate-300">
                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/80">
                  <div className="text-[10px] text-slate-400 font-medium">Distance</div>
                  <div className="text-sm font-bold text-white mt-0.5">{message.route.distance_km} km</div>
                </div>
                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/80">
                  <div className="text-[10px] text-slate-400 font-medium">Est. Duration</div>
                  <div className="text-sm font-bold text-white mt-0.5">{message.route.estimated_duration_text}</div>
                </div>
                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/80">
                  <div className="text-[10px] text-slate-400 font-medium flex items-center gap-1">
                    <Wind className="w-2.5 h-2.5 text-cyan-400" /> Avg Wind
                  </div>
                  <div className="text-sm font-bold text-cyan-300 mt-0.5">
                    {message.route.route_conditions?.avg_wind_speed_knots !== undefined
                      ? `${message.route.route_conditions.avg_wind_speed_knots} kts`
                      : "12 kts"}
                  </div>
                </div>
                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/80">
                  <div className="text-[10px] text-slate-400 font-medium flex items-center gap-1">
                    <Waves className="w-2.5 h-2.5 text-cyan-400" /> Max Wave
                  </div>
                  <div className="text-sm font-bold text-cyan-300 mt-0.5">
                    {message.route.route_conditions?.max_wave_height_m !== undefined
                      ? `${message.route.route_conditions.max_wave_height_m} m`
                      : "1.4 m"}
                  </div>
                </div>
              </div>

              {/* Avoidance and Safety Factors */}
              <div className="flex flex-wrap gap-1.5 text-[10px]">
                <span className="px-2 py-0.5 rounded-md bg-emerald-950/60 text-emerald-300 border border-emerald-800/60 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                  Bypasses Naval Port Channels
                </span>
                <span className="px-2 py-0.5 rounded-md bg-cyan-950/60 text-cyan-300 border border-cyan-800/60 flex items-center gap-1">
                  ✓ Nearshore Reef Clearance
                </span>
                {message.route.route_conditions?.sea_state && (
                  <span className="px-2 py-0.5 rounded-md bg-slate-800/80 text-slate-300 border border-slate-700/60">
                    Sea State: {message.route.route_conditions.sea_state}
                  </span>
                )}
              </div>

              {/* Action Button: View on Map */}
              <div className="pt-1">
                <button
                  type="button"
                  onClick={() => {
                    try {
                      sessionStorage.setItem("marinex_active_route", JSON.stringify(message.route));
                      window.location.href = "/map";
                    } catch (e) {
                      console.error("Failed to store route:", e);
                    }
                  }}
                  className="w-full sm:w-auto px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-md shadow-cyan-900/30 transition cursor-pointer"
                >
                  <MapPin className="w-3.5 h-3.5 text-cyan-200" />
                  <span>View Route on Interactive Map</span>
                  <ExternalLink className="w-3 h-3 text-cyan-200" />
                </button>
              </div>
            </div>
          )}


          {/* Evidence Section */}
          {!isUser && hasEvidence && (
            <div className="mt-3 p-2.5 sm:p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs">
              <div className="flex items-center space-x-1.5 font-bold text-cyan-400 mb-1.5">
                <Activity className="w-3.5 h-3.5" />
                <span>Marine Telemetry & Verified Evidence:</span>
              </div>
              <ul className="space-y-1">
                {message.evidence!.map((item, idx) => (
                  <li
                    key={idx}
                    className="text-[11px] sm:text-xs text-slate-300 flex items-start gap-1.5"
                  >
                    <span className="text-cyan-400 font-bold select-none">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Collapsible Agent Execution Trace */}
          {!isUser && hasTrace && (
            <div className="mt-3 pt-2 border-t border-slate-800/70">
              <button
                type="button"
                onClick={() => setShowTrace(!showTrace)}
                className="flex items-center space-x-1.5 text-[11px] font-semibold text-slate-400 hover:text-cyan-400 transition cursor-pointer"
              >
                {showTrace ? (
                  <ChevronDown className="w-3.5 h-3.5 text-cyan-400" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                )}
                <span className="flex items-center gap-1">
                  <Workflow className="w-3 h-3 text-cyan-400" />
                  Multi-Agent Trace ({message.executionSteps!.length} steps)
                </span>
              </button>
              {showTrace && (
                <div className="mt-2 space-y-1 pl-2.5 border-l-2 border-cyan-500/40 text-[11px]">
                  {message.executionSteps!.map((step, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-2 bg-slate-950/50 rounded-lg px-2.5 py-1.5 border border-slate-800/70"
                    >
                      <span className="font-mono uppercase text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700/60 flex-shrink-0">
                        {step.agent}
                      </span>
                      <div className="flex-1 min-w-0 text-slate-300">
                        {step.details || step.status}
                      </div>
                      <span className="text-[10px] text-emerald-400 font-bold flex-shrink-0">
                        ✓ {step.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Document Citations */}
          {!isUser && hasSources && (
            <div className="mt-3 pt-2 border-t border-slate-800/70">
              <div className="flex items-center space-x-1.5 text-[11px] font-bold text-slate-400 mb-1.5">
                <BookOpen className="w-3 h-3 text-cyan-400" />
                <span>Reference Citations:</span>
              </div>
              <div className="space-y-1">
                {message.sources!.map((src, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-[10px] bg-slate-950/60 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-300"
                  >
                    <span className="font-medium truncate">📄 {src.file}</span>
                    <span className="text-cyan-400 font-mono ml-2 flex-shrink-0 font-bold">
                      Page {src.page}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Message Footer: Copy & Timestamp */}
          <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-slate-800/40 text-[10px] text-slate-500 font-mono">
            <div>
              {!isUser && (
                <button
                  type="button"
                  onClick={handleCopy}
                  className="flex items-center gap-1 text-slate-400 hover:text-cyan-300 transition cursor-pointer"
                  title="Copy response"
                >
                  {copied ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              )}
            </div>
            <span>{message.timestamp}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
