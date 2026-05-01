import React, { useState, useRef, useEffect } from 'react';
import { PlusCircle, MessageSquare, ChevronDown, Check, BarChart3 } from 'lucide-react';

const Sidebar = ({ 
  availableModels, 
  selectedModel, 
  selectedProvider, 
  setSelectedModel, 
  setSelectedProvider, 
  modelName, 
  setModelName,
  currentView,
  setCurrentView
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <aside className="w-64 bg-[#0A0F1D] border-r border-white/10 flex flex-col hidden md:flex z-40 shadow-[10px_0_30px_rgba(0,0,0,0.5)]">
      <div className="p-5 flex-1">
        <button 
          onClick={() => setCurrentView('chat')}
          className={`w-full flex items-center justify-center gap-2 py-2 rounded-xl text-[12px] font-bold transition-all mb-6 ${
            currentView === 'chat' 
            ? 'bg-clinical-blue text-slate-900 shadow-[0_0_20px_rgba(34,211,238,0.3)] hover:scale-[1.02]' 
            : 'bg-white/5 hover:bg-white/10 border border-white/10 text-gray-400'
          }`}
        >
          <PlusCircle size={16} /> New Clinical Query
        </button>
        
        <nav className="space-y-1.5">
          <div className="text-[10px] font-bold text-gray-600 uppercase tracking-[0.3em] px-3 mb-3">Platform Intelligence</div>
          <div 
            onClick={() => setCurrentView('analytics')}
            className={`px-3 py-2.5 rounded-xl flex items-center gap-3.5 text-[12px] font-semibold cursor-pointer transition-all group ${
              currentView === 'analytics'
              ? 'bg-clinical-blue/15 text-clinical-blue border border-clinical-blue/20 shadow-inner'
              : 'text-gray-500 hover:bg-white/5 hover:text-white'
            }`}
          >
            <BarChart3 size={18} className={currentView === 'analytics' ? 'text-clinical-blue' : 'text-gray-600 group-hover:text-gray-300'} />
            <span className="truncate">Agent Performance</span>
          </div>
          
          <div className="pt-6 text-[10px] font-bold text-gray-600 uppercase tracking-[0.3em] px-3 mb-3">Recent Sessions</div>
          <div className="px-4 py-3 bg-white/5 text-gray-300 rounded-xl flex items-center gap-4 text-[12px] font-medium cursor-pointer border border-white/5 shadow-sm">
            <MessageSquare size={18} className="text-clinical-blue/60" />
            <span className="truncate">Department Statistics</span>
          </div>
          <div className="px-4 py-3 hover:bg-white/5 rounded-xl flex items-center gap-4 text-[12px] text-gray-500 cursor-pointer transition-all group">
            <MessageSquare size={18} className="text-gray-700 group-hover:text-gray-400" />
            <span className="truncate">Blood Test Analysis</span>
          </div>
        </nav>
      </div>

      <div className="p-5 border-t border-white/10 flex flex-col gap-3.5 bg-transparent">
        <div className="text-[10px] text-gray-600 font-bold uppercase tracking-[0.3em] mb-1 px-1">Agent Model</div>
        <div className="relative" ref={dropdownRef}>
          <button 
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="w-full flex items-center justify-between bg-slate-800/50 border border-white/10 rounded-xl py-2 px-4 text-[12px] text-clinical-blue font-bold hover:bg-slate-800 transition-all cursor-pointer group shadow-lg"
          >
            <span className="truncate">{modelName || "Select Model"}</span>
            <ChevronDown size={14} className={`transition-transform duration-300 text-gray-500 group-hover:text-clinical-blue ${isDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {isDropdownOpen && (
            <div className="absolute bottom-full left-0 w-full mb-3 bg-[#111827] border border-white/10 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.6)] z-50 max-h-64 overflow-y-auto py-2 backdrop-blur-2xl animate-fade-in">
              {availableModels.map((m, idx) => {
                const isSelected = selectedModel === m.id && selectedProvider === m.provider;
                return (
                  <div 
                    key={idx}
                    onClick={() => {
                      setSelectedProvider(m.provider);
                      setSelectedModel(m.id);
                      setModelName(m.name);
                      setIsDropdownOpen(false);
                    }}
                    className={`flex items-center justify-between px-5 py-2.5 text-[11px] cursor-pointer transition-colors ${
                      isSelected ? 'bg-clinical-blue/20 text-clinical-blue font-bold' : 'text-gray-400 hover:bg-white/5 hover:text-white'
                    }`}
                  >
                    <span className="truncate">{m.name}</span>
                    {isSelected && <Check size={14} className="drop-shadow-[0_0_8px_rgba(34,211,238,0.6)]" />}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </aside>


  );
};

export default Sidebar;
