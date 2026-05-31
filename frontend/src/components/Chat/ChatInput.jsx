import React, { useRef } from 'react';
import { Send } from 'lucide-react';
import EmbeddingStatus from './EmbeddingStatus';

const ChatInput = ({ input, setInput, handleSend, isLoading }) => {
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      handleSend(e);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  return (
    <div className="w-full pt-2.5 pb-2 px-6 flex flex-col items-center border-t border-white/10 bg-[#080C14]/90 backdrop-blur-2xl self-end z-20 shadow-[0_-8px_25px_rgba(0,0,0,0.2)]">
      <div className="w-full max-w-3xl relative">
        <form onSubmit={handleSubmit} className="relative group">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              e.target.style.height = 'auto';
              e.target.style.height = `${e.target.scrollHeight}px`;
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Search clinical records or run analytics..."
            rows={3}
            className="w-full pl-5 pr-14 py-3 bg-slate-900/60 border border-white/10 rounded-md focus:outline-none focus:border-clinical-blue/40 focus:bg-slate-900/90 transition-all duration-300 placeholder:text-gray-600 text-sm text-gray-100 resize-none max-h-64 overflow-y-auto"
          />

          <button
            type="submit"
            className="absolute right-3.5 bottom-3.5 p-2 bg-clinical-blue text-slate-950 rounded-md hover:bg-clinical-blue/80 transition-all cursor-pointer disabled:cursor-not-allowed disabled:opacity-20 flex items-center justify-center"
            disabled={isLoading || !input.trim()}
          >
            <Send size={16} fill="currentColor" />
          </button>
        </form>
        <div className="flex justify-between items-center mt-1.5 text-[9px] text-gray-600 font-bold px-1 uppercase tracking-[0.05em]">
          <p className="flex items-center gap-2">
            AI can make mistakes. Verify critical medical data.
          </p>
          <EmbeddingStatus />
        </div>
      </div>
    </div>


  );
};

export default ChatInput;
