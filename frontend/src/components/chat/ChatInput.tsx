import React, { useState, useRef, useEffect } from "react";
import { Send, Mic } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading = false }) => {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  return (
    <div className="pt-2 border-t border-slate-100 bg-white">
      <div className="flex items-end space-x-2 bg-slate-50 border border-slate-200 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 rounded-xl px-3 py-2 transition">
        {/* Multiline Textarea */}
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about marine conditions, fishing zones, or safety..."
          disabled={isLoading}
          aria-label="Ask about marine conditions"
          className="w-full bg-transparent text-slate-800 placeholder-slate-400 text-xs sm:text-sm focus:outline-none resize-none max-h-28 overflow-y-auto leading-normal py-1"
        />

        <div className="flex items-center space-x-1.5 pb-0.5">
          {/* Voice Input Placeholder */}
          <button
            type="button"
            disabled
            title="Voice input scheduled for future phase"
            aria-label="Voice input"
            className="p-1.5 rounded-lg text-slate-400 bg-slate-100 border border-slate-200 cursor-not-allowed hover:bg-slate-200 transition"
          >
            <Mic className="w-4 h-4 opacity-50" />
          </button>

          {/* Send Button */}
          <button
            type="button"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            aria-label="Send query"
            className="p-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold disabled:opacity-40 disabled:hover:bg-blue-600 disabled:cursor-not-allowed transition shadow-xs cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="flex items-center justify-between px-1 mt-1.5 text-[11px] text-slate-400 font-medium">
        <span>Press <kbd className="font-mono bg-slate-100 border border-slate-200 px-1 py-0.5 rounded text-slate-600">Enter</kbd> to send, <kbd className="font-mono bg-slate-100 border border-slate-200 px-1 py-0.5 rounded text-slate-600">Shift+Enter</kbd> for newline</span>
        <span className="font-mono text-blue-600 font-semibold">ORCA AI</span>
      </div>
    </div>
  );
};

export default ChatInput;
