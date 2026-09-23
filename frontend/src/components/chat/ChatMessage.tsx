import React, { useState } from "react";
import { ChatMessage as ChatMessageType } from "@/types/marine";
import {
  Compass,
  User,
  Sparkles,
  BookOpen,
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
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
          <ShieldCheck className="w-3 h-3 text-emerald-600" /> Risk: LOW (Favorable)
        </span>
      );
    }
    if (r === "MEDIUM") {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
          <AlertTriangle className="w-3 h-3 text-amber-600" /> Risk: MEDIUM (Caution)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
        <AlertOctagon className="w-3 h-3 text-rose-600" /> Risk: HIGH (Hazard)
      </span>
    );
  };

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"} my-2`}>
      <div
        className={`flex max-w-[95%] sm:max-w-[88%] space-x-2.5 ${
          isUser ? "flex-row-reverse space-x-reverse" : "flex-row"
        }`}
      >
        {/* Avatar */}
        <div
          className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
            isUser
              ? "bg-blue-600 text-white"
              : "bg-gradient-to-br from-sky-500 to-blue-700 text-white shadow-xs"
          }`}
        >
          {isUser ? <User className="w-4 h-4" /> : <Compass className="w-4 h-4" />}
        </div>

        {/* Message Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 text-xs sm:text-sm leading-relaxed ${
            isUser
              ? "bg-blue-600 text-white shadow-xs"
              : "bg-white text-slate-800 border border-slate-200 shadow-sm"
          }`}
        >
          {/* AI Header */}
          {!isUser && (
            <div className="flex flex-wrap items-center justify-between gap-1.5 mb-2 pb-1.5 border-b border-slate-100">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="font-bold text-blue-700 text-xs flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" /> MarineX AI
                </span>
                {message.riskLevel ? (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1">
                    <Workflow className="w-2.5 h-2.5" /> Multi-Agent
                  </span>
                ) : message.isRag ? (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200 flex items-center gap-1">
                    <BookOpen className="w-2.5 h-2.5" /> RAG Knowledge Base
                  </span>
                ) : null}
              </div>
            </div>
          )}

          {/* Context and Risk Badges */}
          {!isUser && (message.riskLevel || message.location || message.timeContext) && (
            <div className="flex flex-wrap items-center gap-1.5 mb-2">
              {renderRiskBadge(message.riskLevel)}
              {message.location && (
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                  <MapPin className="w-3 h-3 text-blue-600" /> {message.location}
                </span>
              )}
              {message.timeContext && (
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                  <Clock className="w-3 h-3 text-blue-600" /> {message.timeContext}
                </span>
              )}
            </div>
          )}

          {/* Main Answer Content */}
          <div className="whitespace-pre-line font-normal text-slate-800">
            {message.text}
          </div>

          {/* Evidence Section */}
          {!isUser && hasEvidence && (
            <div className="mt-2.5 p-2.5 rounded-xl bg-slate-50 border border-slate-200/80">
              <div className="flex items-center space-x-1.5 text-[11px] font-bold text-slate-800 mb-1.5">
                <Activity className="w-3.5 h-3.5 text-blue-600" />
                <span>Multi-Agent Evidence & Telemetry:</span>
              </div>
              <ul className="space-y-1">
                {message.evidence!.map((item, idx) => (
                  <li key={idx} className="text-[11px] text-slate-600 flex items-start gap-1.5">
                    <span className="text-blue-500 mt-0.5">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Collapsible Agent Execution Trace */}
          {!isUser && hasTrace && (
            <div className="mt-2.5 pt-2 border-t border-slate-100">
              <button
                onClick={() => setShowTrace(!showTrace)}
                className="flex items-center space-x-1.5 text-[11px] font-semibold text-slate-600 hover:text-blue-700 transition cursor-pointer"
              >
                {showTrace ? (
                  <ChevronDown className="w-3.5 h-3.5 text-blue-600" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                )}
                <span className="flex items-center gap-1">
                  <Workflow className="w-3 h-3 text-blue-600" />
                  Agent Execution Trace ({message.executionSteps!.length} steps)
                </span>
              </button>
              {showTrace && (
                <div className="mt-2 space-y-1 pl-2 border-l-2 border-blue-400 text-[11px]">
                  {message.executionSteps!.map((step, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-2 bg-slate-50 rounded-lg px-2.5 py-1.5 border border-slate-200"
                    >
                      <span className="font-mono uppercase text-[10px] font-bold px-1.5 py-0.5 rounded bg-white text-blue-700 border border-blue-200 flex-shrink-0">
                        {step.agent}
                      </span>
                      <div className="flex-1 min-w-0 text-slate-700">
                        {step.details || step.status}
                      </div>
                      <span className="text-[10px] text-emerald-600 font-bold flex-shrink-0">
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
            <div className="mt-3 pt-2.5 border-t border-slate-100 bg-slate-50 -mx-4 -mb-3 px-4 py-2.5 rounded-b-2xl">
              <div className="flex items-center space-x-1.5 text-[11px] font-bold text-slate-800 mb-1.5">
                <BookOpen className="w-3 h-3 text-blue-600" />
                <span>Document Citations:</span>
              </div>
              <div className="space-y-1">
                {message.sources!.map((src, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-[10px] bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-slate-700"
                  >
                    <span className="font-medium truncate">
                      📄 {src.file}
                    </span>
                    <span className="text-blue-600 font-mono ml-2 flex-shrink-0 font-bold">
                      Page {src.page}
                    </span>
                  </div>
                ))}
              </div>
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
