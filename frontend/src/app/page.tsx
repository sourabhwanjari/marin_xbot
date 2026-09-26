"use client";

import React, { useState, useRef, useEffect } from "react";
import Header from "@/components/layout/Header";
import ChatMessage from "@/components/chat/ChatMessage";
import ChatInput from "@/components/chat/ChatInput";
import { ChatMessage as ChatMessageType } from "@/types/marine";
import { sendChatMessage } from "@/services/api";
import { Compass, RotateCcw } from "lucide-react";

export default function HomePage() {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: ChatMessageType = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: text.trim(),
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    // Extract multi-turn history from current messages
    const history = messages
      .filter((m) => !m.id.startsWith("err-"))
      .map((m) => ({
        role: m.sender === "user" ? ("user" as const) : ("assistant" as const),
        content: m.text,
      }));

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await sendChatMessage(text, history);
      const aiMsg: ChatMessageType = {
        id: `ai-${Date.now()}`,
        sender: "ai",
        text: response.message,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        isDemo: response.is_demo,
        source: response.source,
        sources: response.sources,
        isRag: response.is_rag,
        riskLevel: response.risk_level,
        evidence: response.evidence,
        executionSteps: response.execution_steps,
        location: response.location,
        timeContext: response.time_context,
        route: response.route,
        detected_language: response.detected_language,
        response_language: response.response_language,
        map_data: response.map_data,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error("Chat request failed:", err);
      const errorMsg: ChatMessageType = {
        id: `err-${Date.now()}`,
        sender: "ai",
        text: "Unable to retrieve marine intelligence at this moment. Operating in safe standby. Please try asking again.",
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        isDemo: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetChat = () => {
    setMessages([]);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#070d19] text-slate-100 overflow-hidden">
      {/* Top Navigation Bar: MARINEX AI | Home | Map | About */}
      <Header onNewChat={handleResetChat} />

      {/* Main Conversation Canvas */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {messages.length === 0 ? (
          /* ==================== INITIAL HERO STATE (NO MESSAGES) ==================== */
          <div className="flex-1 flex flex-col items-center justify-center px-4 text-center select-none animate-in fade-in duration-300">
            <div className="max-w-xl mx-auto flex flex-col items-center space-y-4">
              {/* Glowing Emblem */}
              <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-br from-cyan-500 via-sky-600 to-blue-700 flex items-center justify-center text-white shadow-xl shadow-cyan-500/25 border border-cyan-400/30">
                <Compass className="w-9 h-9 sm:w-11 sm:h-11 animate-pulse" />
              </div>

              {/* Title & Subtitle */}
              <div className="space-y-1.5">
                <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
                  MARINEX<span className="text-cyan-400"> AI</span>
                </h1>
                <p className="text-sm sm:text-base font-semibold text-cyan-300/90">
                  Marine Intelligence Assistant
                </p>
                <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto leading-relaxed pt-1">
                  Safe route recommendations, automatic language detection (English, हिन्दी, मराठी), ocean conditions, PFZ, and coastal navigation.
                </p>
              </div>

              {/* Quick Prompt Starters */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full pt-3 max-w-lg text-left">
                <button
                  type="button"
                  onClick={() => handleSendMessage("Recommend a safe route from Chennai to Pulicat")}
                  className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/60 hover:bg-slate-800/80 transition text-xs group cursor-pointer"
                >
                  <div className="font-semibold text-slate-200 group-hover:text-cyan-300 flex items-center gap-1.5">
                    <span>🧭 Recommend Safe Route</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Chennai to Pulicat corridor</div>
                </button>
                <button
                  type="button"
                  onClick={() => handleSendMessage("चेन्नई से पुलिकट सुरक्षित मार्ग बताओ")}
                  className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/60 hover:bg-slate-800/80 transition text-xs group cursor-pointer"
                >
                  <div className="font-semibold text-slate-200 group-hover:text-cyan-300 flex items-center gap-1.5">
                    <span>🇮🇳 हिन्दी में सुरक्षित मार्ग</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">चेन्नई से पुलिकट मार्ग गणना</div>
                </button>
                <button
                  type="button"
                  onClick={() => handleSendMessage("मुंबई ते गोवा सुरक्षित मार्ग दाखवा")}
                  className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/60 hover:bg-slate-800/80 transition text-xs group cursor-pointer"
                >
                  <div className="font-semibold text-slate-200 group-hover:text-cyan-300 flex items-center gap-1.5">
                    <span>🚩 मराठीत सुरक्षित मार्ग</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">मुंबई ते गोवा सागरी मार्ग</div>
                </button>
                <button
                  type="button"
                  onClick={() => handleSendMessage("Is it safe to go fishing tomorrow near Mumbai?")}
                  className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/60 hover:bg-slate-800/80 transition text-xs group cursor-pointer"
                >
                  <div className="font-semibold text-slate-200 group-hover:text-cyan-300 flex items-center gap-1.5">
                    <span>🐟 Fishing Safety Check</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Mumbai swell & wind forecast</div>
                </button>
              </div>
            </div>
          </div>

        ) : (
          /* ==================== ACTIVE CONVERSATION STATE ==================== */
          <div className="flex-1 overflow-y-auto px-3 sm:px-4 py-4 space-y-3 max-w-3xl w-full mx-auto">
            {/* Header controls inside chat area */}
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/60 text-xs text-slate-400">
              <span className="font-semibold text-cyan-400 flex items-center gap-1.5">
                <span>Active Voyage Session</span>
              </span>
              <button
                type="button"
                onClick={handleResetChat}
                className="flex items-center gap-1.5 text-slate-400 hover:text-cyan-300 px-2.5 py-1 rounded-lg hover:bg-slate-800/60 transition cursor-pointer"
                title="Start a new conversation session"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>New Chat</span>
              </button>
            </div>

            {/* Rendered Messages */}
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}

            {/* Loading / Thinking State */}
            {isLoading && (
              <div className="flex items-start gap-3 my-2.5 animate-in fade-in duration-200">
                <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-gradient-to-br from-cyan-500 via-sky-600 to-blue-700 text-white flex items-center justify-center flex-shrink-0 shadow-sm shadow-cyan-500/25">
                  <Compass className="w-4 h-4 animate-spin text-white" />
                </div>
                <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl rounded-tl-xs px-4 py-3 text-sm text-slate-300 shadow-md flex items-center space-x-2">
                  <span className="text-xs text-cyan-300 font-medium">
                    MARINEX AI is analyzing marine conditions
                  </span>
                  <span className="flex space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce"></span>
                    <span
                      className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></span>
                    <span
                      className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce"
                      style={{ animationDelay: "0.4s" }}
                    ></span>
                  </span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} className="h-4" />
          </div>
        )}

        {/* ChatGPT-style Floating Bottom Composer */}
        <div className="w-full bg-gradient-to-t from-[#070d19] via-[#070d19]/95 to-transparent pt-4 pb-2 z-10">
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>
      </main>
    </div>
  );
}
