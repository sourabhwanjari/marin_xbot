import React, { useState, useRef, useEffect } from "react";
import { Send, Mic, MicOff } from "lucide-react";

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
    <div className="pt-2 border-t border-slate-700/60 bg-marine-900/60">
      <div className="flex items-end space-x-2 bg-marine-850/90 border border-slate-700/80 focus-within:border-cyan-500/60 rounded-xl px-3 py-2 transition shadow-inner">
        {/* Multiline Textarea */}
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about marine conditions..."
          disabled={isLoading}
          aria-label="Ask about marine conditions"
          className="w-full bg-transparent text-slate-100 placeholder-slate-400 text-xs sm:text-sm focus:outline-none resize-none max-h-28 overflow-y-auto leading-normal py-1"
        />

        <div className="flex items-center space-x-1.5 pb-0.5">
          {/* Voice Input Placeholder (Disabled in Phase 1) */}
          <button
            type="button"
            disabled
            title="Voice input scheduled for Phase 4"
            aria-label="Voice input (Disabled in Phase 1)"
            className="p-1.5 rounded-lg text-slate-500 bg-slate-800/60 border border-slate-700/40 cursor-not-allowed hover:bg-slate-800 transition"
          >
            <Mic className="w-4 h-4 opacity-60" />
          </button>

          {/* Send Button */}
          <button
            type="button"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            aria-label="Send query"
            className="p-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-marine-950 font-bold disabled:opacity-40 disabled:hover:bg-cyan-500 disabled:cursor-not-allowed transition shadow-marine-cyan"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="flex items-center justify-between px-1 mt-1 text-[10px] text-slate-400">
        <span>Press <kbd className="font-mono bg-slate-800 px-1 py-0.5 rounded text-slate-300">Enter</kbd> to send, <kbd className="font-mono bg-slate-800 px-1 py-0.5 rounded text-slate-300">Shift+Enter</kbd> for new line</span>
        <span className="font-mono text-cyan-400/80">Phase 1 Demo</span>
      </div>
    </div>
  );
};
export default ChatInput;
