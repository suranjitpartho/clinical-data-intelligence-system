import React from 'react';
import { Bot } from 'lucide-react';

const Header = () => {
  return (
    <header className="w-full border-b border-white/10 bg-[#0F172A]/80 backdrop-blur-xl z-50 p-3.5 px-6 flex justify-between items-center shadow-xl">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 pr-6 border-r border-white/10">
          <div className="relative">
            <Bot className="text-clinical-blue animate-beep relative z-10" size={22} />
            <div className="absolute inset-0 bg-clinical-blue/30 blur-xl rounded-full animate-glow-pulse"></div>
          </div>
          <h1 className="font-display font-bold tracking-tight text-lg text-white">
            Clinical Data <span className="text-clinical-blue">Intelligence System</span>
          </h1>
        </div>
      </div>
      <div className="flex items-center gap-6">
        <div className="text-xs text-right">
          <div className="font-bold text-gray-100 text-[13px]">Suranjit Das</div>
          <div className="text-gray-500 font-semibold uppercase tracking-wider text-[10px]">AI System Engineer</div>
        </div>
        <div className="w-10 h-10 rounded-xl bg-slate-800 border border-white/10 flex items-center justify-center text-white text-xs font-bold shadow-[inset_0_2px_4px_rgba(255,255,255,0.05)]">
          SD
        </div>
      </div>
    </header>


  );
};

export default Header;
