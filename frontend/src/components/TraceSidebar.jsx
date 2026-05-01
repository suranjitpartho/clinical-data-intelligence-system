import React from 'react';
import { X, Brain, Info } from 'lucide-react';

const TraceSidebar = ({ isOpen, setIsOpen, logs }) => {
  return (
    <div 
      className={`h-full bg-slate-900/60 backdrop-blur-2xl border-l border-white/5 transition-all duration-500 ease-in-out flex flex-col overflow-hidden z-[100] ${
        isOpen ? 'w-[320px]' : 'w-0 border-l-0'
      }`}
    >
      {/* Header */}
      <div className="p-4 border-b border-white/5 flex items-center justify-between bg-black/20">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-clinical-blue/10 rounded-lg border border-clinical-blue/20">
            <Brain size={16} className="text-clinical-blue" />
          </div>
          <div>
            <h3 className="text-[11px] font-bold text-white uppercase tracking-[0.2em]">Reasoning Trace</h3>
            <p className="text-[9px] text-gray-600 font-semibold tracking-tight uppercase">Decision Logic</p>
          </div>
        </div>
        <button 
          onClick={() => setIsOpen(false)}
          className="p-1.5 hover:bg-white/5 rounded-full transition-all text-gray-600 hover:text-white"
        >
          <X size={16} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5 custom-scrollbar flex flex-col space-y-5">
        {logs ? (
          <div className="animate-fade-in flex flex-col h-full">
            <div className="space-y-6 flex-1">
              <div className="text-[12px] leading-relaxed text-gray-400 italic whitespace-pre-wrap font-medium">
                {logs.replace(/\*/g, '•')}
              </div>
            </div>

            <div className="mt-6 flex items-start gap-3 p-4 bg-white/5 rounded-xl border border-white/10 shadow-inner">
              <Info size={14} className="text-clinical-blue/40 mt-1 shrink-0" />
              <p className="text-[10px] text-gray-500 font-medium leading-relaxed italic">
                This trace details the agent's internal clinical strategy, including database joins and self-correction steps.
              </p>
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-4">
             <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center border border-white/5">
                <Brain size={28} className="text-gray-700" />
             </div>
             <p className="text-[12px] text-gray-500 font-bold uppercase tracking-widest">Awaiting Analysis</p>
             <p className="text-[11px] text-gray-600 max-w-[200px]">Select a "Reasoning Trace" tag in the chat to inspect the underlying strategy.</p>
          </div>
        )}
      </div>
    </div>

  );
};

export default TraceSidebar;
