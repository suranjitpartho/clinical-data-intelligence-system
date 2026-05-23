import React, { useState, useRef, useEffect } from 'react';
import { PlusCircle, MessageSquare, ChevronDown, Check, BarChart3, Clock } from 'lucide-react';

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
  onNewChat,
  threads,
  activeThreadId,
  onSelectThread
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

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now - d;
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    return d.toLocaleDateString();
  };

  const isActive = (tid) => tid === activeThreadId && currentView === 'chat';

  return (
    <aside className="w-64 bg-[#0A0F1D] border-r border-white/10 flex flex-col hidden md:flex z-40">
      <div className="p-5 flex-1 flex flex-col overflow-hidden">
        <button
          type="button"
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-[12px] font-bold transition-all mb-3 bg-clinical-blue text-slate-900 hover:bg-clinical-blue/90 cursor-pointer active:bg-clinical-blue/80"
        >
          <PlusCircle size={16} /> Create New Chat
        </button>

        <div
          onClick={() => setCurrentView('analytics')}
          className={`px-4 py-2.5 rounded-md flex items-center gap-3.5 text-[12px] font-semibold cursor-pointer transition-colors group mb-7 ${currentView === 'analytics'
              ? 'bg-clinical-blue/10 text-clinical-blue border border-clinical-blue/20'
              : 'text-gray-400 hover:bg-white/5 hover:text-gray-100'
            }`}
        >
          <BarChart3 size={18} className={currentView === 'analytics' ? 'text-clinical-blue' : 'text-gray-500 group-hover:text-clinical-blue/70'} />
          <span className="truncate">Observability Dashboard</span>
        </div>

        {threads.length > 0 && (
          <div className="flex-1 overflow-y-auto min-h-0 mb-4">
            <div className="text-[10px] font-bold text-gray-600 uppercase tracking-[0.3em] px-4 mb-3">
              Conversations
            </div>
            <div className="space-y-0.5">
              {threads.map((t) => (
                <div
                  key={t.thread_id}
                  onClick={() => onSelectThread(t.thread_id)}
                  className={`px-4 py-2.5 rounded-md flex items-center gap-3 text-[12px] font-medium cursor-pointer transition-colors group ${
                    isActive(t.thread_id)
                      ? 'bg-clinical-blue/10 text-clinical-blue border border-clinical-blue/20'
                      : 'text-gray-400 hover:bg-white/5 hover:text-gray-100'
                  }`}
                >
                  <MessageSquare
                    size={14}
                    className={
                      isActive(t.thread_id)
                        ? 'text-clinical-blue shrink-0'
                        : 'text-gray-500 group-hover:text-clinical-blue/70 shrink-0'
                    }
                  />
                  <div className="truncate min-w-0 flex-1">
                    <div className="truncate">{t.title}</div>
                    <div className="flex items-center gap-1 text-[10px] text-gray-600 mt-0.5">
                      <Clock size={10} />
                      <span>{formatDate(t.created_at)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
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
