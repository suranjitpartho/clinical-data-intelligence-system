import React from 'react';
import { X, Brain, Info } from 'lucide-react';

const TraceSidebar = ({ isOpen, setIsOpen, logs }) => {
  return (
    <div 
      className={`h-full bg-white border-l border-gray-100 transition-all duration-500 ease-in-out flex flex-col overflow-hidden ${
        isOpen ? 'w-[400px]' : 'w-0 border-l-0'
      }`}
    >
      {/* Header */}
      <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-white">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gray-50 rounded-lg">
            <Brain size={18} className="text-dark-grey" />
          </div>
          <div>
            <h3 className="text-[11px] font-bold text-dark-grey uppercase tracking-widest">Reasoning Trace</h3>
            <p className="text-[9px] text-gray-400 font-medium tracking-tight">AI STRATEGY & CLINICAL LOGIC</p>
          </div>
        </div>
        <button 
          onClick={() => setIsOpen(false)}
          className="p-2 hover:bg-gray-50 rounded-full transition-colors text-gray-300 hover:text-dark-grey"
        >
          <X size={20} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 bg-white custom-scrollbar flex flex-col">
        {logs ? (
          <div className="animate-fade-in flex flex-col h-full">
            <div className="space-y-4 flex-1">
              <div className="text-[13px] leading-[1.7] text-gray-500 italic whitespace-pre-wrap">
                {logs.replace(/\*/g, '•')}
              </div>
            </div>

            <div className="mt-8 flex items-start gap-3 p-4 bg-gray-50/50 rounded-xl border border-gray-100">
              <Info size={14} className="text-gray-400 mt-1 shrink-0" />
              <p className="text-[11px] text-gray-400 italic leading-relaxed">
                Internal clinical strategy and database join logic used by the agent.
              </p>
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-3">
             <div className="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center">
                <Brain size={24} className="text-gray-200" />
             </div>
             <p className="text-[11px] text-gray-400 font-medium">Click a "Reasoning Trace" tag to view strategy.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TraceSidebar;
