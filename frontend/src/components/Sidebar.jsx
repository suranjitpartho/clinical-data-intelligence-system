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
  setCurrentView,
  onNewChat
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
    <aside className="w-64 bg-[#0A0F1D] border-r border-white/10 flex flex-col hidden md:flex z-40">
      <div className="p-5 flex-1">
        <button
          type="button"
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-[12px] font-bold transition-all mb-8 bg-clinical-blue text-slate-900 hover:bg-clinical-blue/90 cursor-pointer active:bg-clinical-blue/80"
        >
          <PlusCircle size={16} /> Create New Chat
        </button>

        <nav className="space-y-1">
          <div className="text-[10px] font-bold text-gray-600 uppercase tracking-[0.3em] px-4 mb-4">Navigation</div>
          
          <div
            onClick={() => setCurrentView('chat')}
            className={`px-4 py-2.5 rounded-md flex items-center gap-3.5 text-[12px] font-semibold cursor-pointer transition-colors group ${currentView === 'chat'
                ? 'bg-clinical-blue/10 text-clinical-blue border border-clinical-blue/20'
                : 'text-gray-400 hover:bg-white/5 hover:text-gray-100'
              }`}
          >
            <MessageSquare size={18} className={currentView === 'chat' ? 'text-clinical-blue' : 'text-gray-500 group-hover:text-clinical-blue/70'} />
            <span className="truncate">Current Chat Session</span>
          </div>

          <div
            onClick={() => setCurrentView('analytics')}
            className={`px-4 py-2.5 rounded-md flex items-center gap-3.5 text-[12px] font-semibold cursor-pointer transition-colors group ${currentView === 'analytics'
                ? 'bg-clinical-blue/10 text-clinical-blue border border-clinical-blue/20'
                : 'text-gray-400 hover:bg-white/5 hover:text-gray-100'
              }`}
          >
            <BarChart3 size={18} className={currentView === 'analytics' ? 'text-clinical-blue' : 'text-gray-500 group-hover:text-clinical-blue/70'} />
            <span className="truncate">Observability Dashboard</span>
          </div>
        </nav>
      </div>

      <div className="p-5 border-t border-white/10 flex flex-col gap-3.5 bg-transparent">
        <div className="text-[10px] text-gray-600 font-bold uppercase tracking-[0.3em] mb-1 px-1">Agent Model</div>
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="w-full flex items-center justify-between bg-slate-800/50 border border-white/10 rounded-md py-2 px-4 text-[12px] text-clinical-blue font-bold hover:bg-slate-800 transition-all cursor-pointer group"
          >
            <span className="truncate">{modelName || "Select Model"}</span>
            <ChevronDown size={14} className={`transition-transform duration-300 text-gray-500 group-hover:text-clinical-blue ${isDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {isDropdownOpen && (
            <div className="absolute bottom-full left-0 w-full mb-3 bg-[#111827] border border-white/10 rounded-lg shadow-2xl z-50 max-h-64 overflow-y-auto py-2 animate-fade-in">
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
                    className={`flex items-center justify-between px-5 py-2.5 text-[11px] cursor-pointer transition-colors ${isSelected ? 'bg-clinical-blue/20 text-clinical-blue font-bold' : 'text-gray-400 hover:bg-white/5 hover:text-white'
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
