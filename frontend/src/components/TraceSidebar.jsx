import React from 'react';
import { X, Brain, Info } from 'lucide-react';

const TraceSidebar = ({ isOpen, setIsOpen, logs }) => {
  return (
    <>
      {/* Backdrop for click-outside-to-close */}
      <div 
        className={`fixed inset-0 bg-black/5 transition-opacity duration-500 z-40 ${
          isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={() => setIsOpen(false)}
      />

      <div 
        className={`fixed top-0 right-0 h-full w-[400px] bg-white border-l border-gray-100 shadow-2xl transition-transform duration-500 ease-in-out z-50 flex flex-col ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
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
              <div className="text-[13px] leading-[1.6] text-dark-grey whitespace-pre-wrap">
                {logs}
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
    </>
  );
};

export default TraceSidebar;
