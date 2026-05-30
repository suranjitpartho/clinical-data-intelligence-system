import React, { useState, useRef, useEffect } from 'react';
import { PlusCircle, MessageSquare, ChevronDown, Check, BarChart3, Clock, ChevronLeft, ChevronRight } from 'lucide-react';

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
  hasMore,
  currentPage,
  onPageChange,
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
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top section with padding for items above scroll */}
        <div className="px-4 pt-4 pb-3 space-y-2">
          <button
            type="button"
            onClick={onNewChat}
            className="w-full flex items-center justify-center gap-2 py-2 rounded-md text-[12px] font-bold transition-all bg-clinical-blue text-slate-900 hover:bg-clinical-blue/90 cursor-pointer active:bg-clinical-blue/80"
          >
            <PlusCircle size={16} /> Create New Chat
          </button>

          <div
            onClick={() => setCurrentView('analytics')}
            className={`px-3 py-2 rounded-md flex items-center gap-3 text-[12px] font-semibold cursor-pointer transition-colors group ${
              currentView === 'analytics'
                ? 'bg-clinical-blue/10 text-clinical-blue'
                : 'text-gray-400 hover:bg-white/5 hover:text-gray-100'
            }`}
          >
            <BarChart3 size={16} className={currentView === 'analytics' ? 'text-clinical-blue' : 'text-gray-500 group-hover:text-clinical-blue/70'} />
            <span className="truncate">Observability Dashboard</span>
          </div>
        </div>

        {threads.length > 0 && (
          <div className="flex-1 overflow-y-auto min-h-0 custom-scrollbar pt-3">
            <div className="text-[10px] font-bold text-gray-600 uppercase tracking-[0.3em] px-4 pb-1.5">
              Conversations
            </div>
            <div className="space-y-px">
              {threads.map((t) => (
                <div
                  key={t.thread_id}
                  onClick={() => onSelectThread(t.thread_id)}
                  className={`flex items-center gap-2.5 px-4 py-2 text-[12px] font-medium cursor-pointer transition-colors group ${
                    isActive(t.thread_id)
                      ? 'bg-clinical-blue/10 text-clinical-blue'
                      : 'text-gray-400 hover:bg-white/5 hover:text-gray-100'
                  }`}
                >
                  <MessageSquare
                    size={13}
                    className={
                      isActive(t.thread_id)
                        ? 'text-clinical-blue shrink-0'
                        : 'text-gray-500 group-hover:text-clinical-blue/70 shrink-0'
                    }
                  />
                  <div className="truncate min-w-0 flex-1">
                    <div className="truncate">{t.title}</div>
                    <div className="flex items-center gap-1 text-[10px] text-gray-600">
                      <Clock size={9} />
                      <span>{formatDate(t.created_at)}</span>
                    </div>
                  </div>
                </div>
              ))}
              <div className="flex items-center justify-between px-4 py-2 mt-1">
                <button
                  onClick={() => onPageChange(currentPage - 1)}
                  disabled={currentPage <= 1}
                  className="flex items-center gap-1 text-[10px] font-bold text-gray-500 hover:text-clinical-blue disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
                >
                  <ChevronLeft size={12} />
                  Prev
                </button>
                <span className="text-[9px] font-bold text-gray-600 tracking-wider">Page {currentPage}</span>
                <button
                  onClick={() => onPageChange(currentPage + 1)}
                  disabled={!hasMore}
                  className="flex items-center gap-1 text-[10px] font-bold text-gray-500 hover:text-clinical-blue disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
                >
                  Next
                  <ChevronRight size={12} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="px-4 py-3 border-t border-white/10 flex flex-col gap-2.5 bg-transparent">
        <div className="text-[10px] text-gray-600 font-bold uppercase tracking-[0.3em]">Agent Model</div>
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="w-full flex items-center justify-between bg-slate-800/50 border border-white/10 rounded-md py-1.5 px-3 text-[12px] text-clinical-blue font-bold hover:bg-slate-800 transition-all cursor-pointer group"
          >
            <span className="truncate">{modelName || "Select Model"}</span>
            <ChevronDown size={13} className={`transition-transform duration-300 text-gray-500 group-hover:text-clinical-blue ${isDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {isDropdownOpen && (
            <div className="absolute bottom-full left-0 w-full mb-2 bg-[#111827] border border-white/10 rounded-lg shadow-2xl z-50 max-h-60 overflow-y-auto py-1.5 animate-fade-in">
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
                    className={`flex items-center justify-between px-4 py-2 text-[11px] cursor-pointer transition-colors ${isSelected ? 'bg-clinical-blue/20 text-clinical-blue font-bold' : 'text-gray-400 hover:bg-white/5 hover:text-white'
                      }`}
                  >
                    <span className="truncate">{m.name}</span>
                    {isSelected && <Check size={13} className="drop-shadow-[0_0_8px_rgba(34,211,238,0.6)]" />}
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
