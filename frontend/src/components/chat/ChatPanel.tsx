"use client";

import React, { useState, useRef, useEffect } from "react";
import { ChatMessage as ChatMessageType } from "@/types/marine";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import { Bot, RefreshCw, Sparkles } from "lucide-react";
import { sendChatMessage } from "@/services/api";

interface ChatPanelProps {
  onActionSelect?: (action: string) => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ onActionSelect }) => {
  const [messages, setMessages] = useState<ChatMessageType[]>([
    {
      id: "initial-01",
      sender: "ai",
      text: "Welcome to MARINEX AI — Marine Intelligence & Decision Support.\n\nI can assist you with Potential Fishing Zones (PFZ), ocean sea-state forecasts, wind and swell hazards, and coastal geofencing.\n\nWhat would you like to investigate today?",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      isDemo: true,
      source: "mock-data",
    },
  ]);

  const [isLoading, setIsLoading] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (text: string) => {
    const userMsg: ChatMessageType = {
      id: `user-${Date.now()}`,
      sender: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const history = messages
      .filter((m) => m.id !== "initial-01" && !m.id.startsWith("err-"))
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
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isDemo: response.is_demo,
        source: response.source,
        suggestedActions: response.suggested_actions,
        relatedZones: response.related_zones,
        sources: response.sources,
        isRag: response.is_rag,
        retrievedChunks: response.retrieved_chunks,
        riskLevel: response.risk_level,
        evidence: response.evidence,
        executionSteps: response.execution_steps,
        location: response.location,
        timeContext: response.time_context,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      const errorMsg: ChatMessageType = {
        id: `err-${Date.now()}`,
        sender: "ai",
        text: "Error retrieving marine intelligence. Operating in offline demonstration mode. Please try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isDemo: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleActionClick = (action: string) => {
    if (onActionSelect) onActionSelect(action);
    handleSendMessage(action);
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Panel Header */}
      <div className="p-3.5 border-b border-slate-100 bg-white flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
              <span>Marine Intelligence</span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                AI Agent
              </span>
            </h2>
            <p className="text-[11px] text-slate-500">
              Ask about fishing zones, weather, and ocean safety.
            </p>
          </div>
        </div>

        <button
          onClick={() =>
            setMessages([
              {
                id: `reset-${Date.now()}`,
                sender: "ai",
                text: "Chat context refreshed. Ask about Potential Fishing Zones, weather, or marine safety.",
                timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                isDemo: true,
              },
            ])
          }
          title="Clear & Reset Chat"
          aria-label="Clear chat"
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 border border-transparent transition cursor-pointer"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto overscroll-contain p-3.5 bg-slate-50/50 space-y-2"
      >
        {messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            message={msg}
            onActionClick={handleActionClick}
          />
        ))}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-center space-x-2 py-2 px-3 bg-white rounded-xl border border-slate-200 text-blue-600 text-xs font-medium w-fit shadow-xs">
            <div className="w-3.5 h-3.5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span>Reasoning over satellite SST & oceanographic telemetry...</span>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-3 bg-white border-t border-slate-100 shrink-0">
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default ChatPanel;
