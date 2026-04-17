import React, { useState, useRef, useEffect } from 'react';
import { PlusCircle, MessageSquare, ChevronDown, Check } from 'lucide-react';

const Sidebar = ({ 
  availableModels, 
  selectedModel, 
  selectedProvider, 
  setSelectedModel, 
  setSelectedProvider, 
  modelName, 
  setModelName 
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
    <aside className="w-64 bg-white border-r border-gray-100 flex flex-col hidden md:flex">
      <div className="p-4 flex-1">
        <button className="w-full flex items-center justify-center gap-2 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-100 rounded-lg text-sm font-medium transition-all mb-6">
          <PlusCircle size={16} /> New Consultation
        </button>
        
        <nav className="space-y-1">
          <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-3 mb-2">Recent</div>
          <div className="px-3 py-2 bg-blue-50/50 text-clinical-blue rounded-md flex items-center gap-3 text-sm font-medium cursor-pointer">
            <MessageSquare size={16} />
            <span className="truncate">Department Statistics</span>
          </div>
          <div className="px-3 py-2 hover:bg-gray-50 rounded-md flex items-center gap-3 text-sm text-gray-600 cursor-pointer">
            <MessageSquare size={16} />
            <span className="truncate">Blood Test Analysis</span>
          </div>
        </nav>
      </div>

      <div className="p-4 border-t border-gray-50 flex flex-col gap-2 bg-gray-50/30">
        <div className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-1">Model</div>
        <div className="relative" ref={dropdownRef}>
          <button 
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="w-full flex items-center justify-between bg-white border border-gray-100 rounded-md py-1.5 px-2 text-[12px] text-clinical-blue font-medium hover:bg-gray-50 transition-all cursor-pointer"
          >
            <span className="truncate">{modelName || "Select Model"}</span>
            <ChevronDown size={14} className={`transition-transform duration-200 ${isDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {isDropdownOpen && (
            <div className="absolute bottom-full left-0 w-full mb-1 bg-white border border-gray-100 rounded-lg shadow-xl z-30 max-h-48 overflow-y-auto py-1 animate-fade-in">
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
                    className={`flex items-center justify-between px-3 py-1.5 text-[11px] cursor-pointer transition-colors ${
                      isSelected ? 'bg-blue-50 text-clinical-blue font-bold' : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    <span className="truncate">{m.name}</span>
                    {isSelected && <Check size={12} />}
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
