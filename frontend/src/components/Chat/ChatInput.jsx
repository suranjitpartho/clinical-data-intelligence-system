import React, { useRef } from 'react';
import { Send } from 'lucide-react';

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
    <div className="w-full pt-4 pb-4 px-6 flex flex-col items-center border-t border-gray-100 bg-off-white/80 backdrop-blur-sm self-end">
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
            placeholder="Query clinical data..." 
            rows={1}
            className="w-full pl-6 pr-16 pt-4 pb-14 bg-white border border-gray-100 rounded-2xl focus:outline-none focus:shadow-[0_12px_20px_-5px_rgba(0,0,0,0.1),0_4px_6px_-2px_rgba(0,0,0,0.05)] focus:-translate-y-0.5 transition-all duration-300 placeholder:text-gray-300 resize-none max-h-64 overflow-y-hidden"
          />

          <button 
            type="submit"
            className="absolute right-3 bottom-5 p-2 bg-clinical-blue text-white rounded-md hover:brightness-90 transition-all cursor-pointer disabled:cursor-not-allowed disabled:opacity-40 flex items-center justify-center shadow-sm" 
            disabled={isLoading || !input.trim()}
          >
            <Send size={18} fill="white" />
          </button>
        </form>
        <div className="flex justify-between items-center mt-3 text-[10px] text-gray-400">
          <p>Clinical AI can make mistakes. Check important info.</p>
          <div className="flex items-center gap-2">
            <span>Build v1.2.5 • Stable</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
