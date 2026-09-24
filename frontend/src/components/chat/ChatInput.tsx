"use client";

import React, { useState, useRef, useEffect } from "react";
import { ArrowUp, Loader2 } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading = false,
}) => {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    const textToSend = input.trim();
    setInput("");
    onSendMessage(textToSend);

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-resize textarea smoothly
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        140
      )}px`;
    }
  }, [input]);

  const canSubmit = input.trim().length > 0 && !isLoading;

  return (
    <div className="w-full max-w-3xl mx-auto px-3 sm:px-4">
      {/* ChatGPT-style Floating Capsule Composer */}
      <div className="relative bg-slate-900/95 border border-slate-700/80 rounded-2xl sm:rounded-3xl p-2 sm:p-2.5 shadow-2xl focus-within:border-cyan-500/80 focus-within:ring-2 focus-within:ring-cyan-500/20 transition-all flex items-end gap-2">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask MARINEX about marine conditions, weather, PFZ, or safety..."
          disabled={isLoading}
          aria-label="Ask MARINEX about marine conditions"
          className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-xs sm:text-sm focus:outline-none resize-none max-h-36 overflow-y-auto leading-relaxed py-1.5 px-2"
        />

        {/* Circular Send Button (ChatGPT-style) */}
        <button
          type="button"
          onClick={handleSend}
          disabled={!canSubmit}
          aria-label="Send message"
          className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all ${
            canSubmit
              ? "bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold shadow-md shadow-cyan-500/30 cursor-pointer transform hover:scale-105 active:scale-95"
              : "bg-slate-800 text-slate-500 cursor-not-allowed"
          }`}
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
          ) : (
            <ArrowUp className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Subtle Micro Disclaimer */}
      <div className="text-center py-2 text-[10px] sm:text-[11px] text-slate-500 select-none">
        MARINEX AI provides marine decision support. Always consult official Coast Guard & IMD bulletins.
      </div>
    </div>
  );
};

export default ChatInput;
