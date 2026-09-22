import React, { useState } from "react";
import { ChatMessage as ChatMessageType } from "@/types/marine";
import {
  Compass,
  User,
  Sparkles,
  BookOpen,
  Layers,
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  ChevronDown,
  ChevronRight,
  Activity,
  MapPin,
  Clock,
  Workflow,
} from "lucide-react";

interface ChatMessageProps {
  message: ChatMessageType;
  onActionClick?: (action: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onActionClick }) => {
  const isUser = message.sender === "user";
  const hasSources = message.sources && message.sources.length > 0;
  const hasEvidence = message.evidence && message.evidence.length > 0;
  const hasTrace = message.executionSteps && message.executionSteps.length > 0;
  const [showTrace, setShowTrace] = useState(false);

  const renderRiskBadge = (risk?: string) => {
    if (!risk) return null;
    const r = risk.toUpperCase();
    if (r === "LOW") {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
          <ShieldCheck className="w-3 h-3" /> Risk: LOW (Favorable)
        </span>
      );
    }
    if (r === "MEDIUM") {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40">
          <AlertTriangle className="w-3 h-3" /> Risk: MEDIUM (Caution)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40">
        <AlertOctagon className="w-3 h-3" /> Risk: HIGH (Hazard)
      </span>
    );
  };

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"} my-2.5`}>
      <div
        className={`flex max-w-[95%] sm:max-w-[88%] space-x-2.5 ${
          isUser ? "flex-row-reverse space-x-reverse" : "flex-row"
        }`}
      >
        {/* Avatar */}
        <div
          className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
            isUser
              ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400/40"
              : "bg-marine-800 text-cyan-400 border border-cyan-500/30 shadow-marine-cyan"
          }`}
        >
          {isUser ? <User className="w-4 h-4" /> : <Compass className="w-4 h-4" />}
        </div>

        {/* Message Bubble */}
        <div
          className={`rounded-xl px-3.5 py-2.5 text-xs sm:text-sm leading-relaxed ${
            isUser
              ? "bg-marine-700/80 text-white border border-cyan-500/30 shadow-sm"
              : "bg-marine-850/90 text-slate-200 border border-slate-700/70 shadow-marine-card"
          }`}
        >
          {/* AI Header with Multi-Agent / RAG / Source Badges */}
          {!isUser && (
            <div className="flex flex-wrap items-center justify-between gap-1.5 mb-2 pb-1.5 border-b border-slate-700/50">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="font-semibold text-cyan-400 text-xs flex items-center gap-1">
                  <Sparkles className="w-3 h-3" /> MarineX AI
                </span>
                {message.riskLevel ? (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 flex items-center gap-1">
                    <Workflow className="w-2.5 h-2.5" /> Multi-Agent Orchestrator
                  </span>
                ) : message.isRag ? (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40 flex items-center gap-1">
                    <BookOpen className="w-2.5 h-2.5" /> RAG Knowledge Base
                  </span>
                ) : (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                    <Layers className="w-2.5 h-2.5" /> Live Marine Data
                  </span>
                )}
              </div>
              <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                DEMO DATA
              </span>
            </div>
          )}

          {/* Context and Risk Badges */}
          {!isUser && (message.riskLevel || message.location || message.timeContext) && (
            <div className="flex flex-wrap items-center gap-1.5 mb-2">
              {renderRiskBadge(message.riskLevel)}
              {message.location && (
                <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  <MapPin className="w-3 h-3 text-cyan-400" /> {message.location}
                </span>
              )}
              {message.timeContext && (
                <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  <Clock className="w-3 h-3 text-blue-400" /> {message.timeContext}
                </span>
              )}
            </div>
          )}

          {/* Main Answer Content */}
          <div className="whitespace-pre-line text-slate-100 font-normal">
            {message.text}
          </div>

          {/* Evidence Section */}
          {!isUser && hasEvidence && (
            <div className="mt-2.5 p-2.5 rounded-lg bg-marine-900/60 border border-slate-700/60">
              <div className="flex items-center space-x-1.5 text-[11px] font-semibold text-cyan-300 mb-1.5">
                <Activity className="w-3.5 h-3.5 text-cyan-400" />
                <span>Multi-Agent Evidence & Telemetry:</span>
              </div>
              <ul className="space-y-1">
                {message.evidence!.map((item, idx) => (
                  <li key={idx} className="text-[11px] text-slate-300 flex items-start gap-1.5">
                    <span className="text-cyan-400 mt-0.5">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Collapsible Agent Execution Trace */}
          {!isUser && hasTrace && (
            <div className="mt-2.5 pt-2 border-t border-slate-700/50">
              <button
                onClick={() => setShowTrace(!showTrace)}
                className="flex items-center space-x-1.5 text-[11px] font-medium text-slate-300 hover:text-cyan-300 transition cursor-pointer"
              >
                {showTrace ? (
                  <ChevronDown className="w-3.5 h-3.5 text-cyan-400" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                )}
                <span className="flex items-center gap-1">
                  <Workflow className="w-3 h-3 text-cyan-400" />
                  Agent Execution Trace ({message.executionSteps!.length} steps)
                </span>
              </button>
              {showTrace && (
                <div className="mt-2 space-y-1 pl-2 border-l-2 border-cyan-500/40 text-[11px]">
                  {message.executionSteps!.map((step, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-2 bg-marine-800/70 rounded px-2 py-1 border border-slate-700/40"
                    >
                      <span className="font-mono uppercase text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60 flex-shrink-0">
                        {step.agent}
                      </span>
                      <div className="flex-1 min-w-0 text-slate-300">
                        {step.details || step.status}
                      </div>
                      <span className="text-[10px] text-emerald-400 font-mono flex-shrink-0">
                        ✓ {step.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Source Citations Section */}
          {!isUser && hasSources && (
            <div className="mt-3 pt-2.5 border-t border-slate-700/60 bg-marine-900/40 -mx-3.5 -mb-2.5 px-3.5 py-2 rounded-b-xl">
              <div className="flex items-center space-x-1.5 text-[11px] font-semibold text-cyan-300 mb-1.5">
                <BookOpen className="w-3 h-3 text-cyan-400" />
                <span>Document Citations:</span>
              </div>
              <div className="space-y-1">
                {message.sources!.map((src, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-[10px] bg-marine-800/80 border border-slate-700/60 rounded px-2 py-1 text-slate-300"
                  >
                    <span className="font-medium text-slate-200 truncate">
                      📄 {src.file}
                    </span>
                    <span className="text-cyan-400 font-mono ml-2 flex-shrink-0">
                      Page {src.page}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Chips */}
          {!isUser && message.suggestedActions && message.suggestedActions.length > 0 && (
            <div className="mt-3 pt-2 border-t border-slate-700/50 flex flex-wrap gap-1.5">
              {message.suggestedActions.map((action, idx) => (
                <button
                  key={idx}
                  onClick={() => onActionClick && onActionClick(action)}
                  className="text-[11px] px-2 py-0.5 rounded bg-cyan-950/60 hover:bg-cyan-900/80 text-cyan-300 border border-cyan-600/40 hover:border-cyan-400 transition cursor-pointer"
                >
                  ⚡ {action}
                </button>
              ))}
            </div>
          )}

          {/* Timestamp */}
          <div className="text-[10px] text-slate-400 text-right mt-1.5 font-mono">
            {message.timestamp}
          </div>
        </div>
      </div>
    </div>
  );
};
export default ChatMessage;
