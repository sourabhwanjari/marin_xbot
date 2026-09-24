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
