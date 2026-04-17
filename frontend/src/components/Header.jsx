import React from 'react';
import { Bot } from 'lucide-react';

const Header = () => {
  return (
    <header className="w-full border-b border-gray-100 bg-white/80 backdrop-blur-sm z-20 p-4 px-8 flex justify-between items-center">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 pr-6 border-r border-gray-100">
          <Bot className="text-clinical-blue animate-beep" size={24} />
          <h1 className="font-display font-medium tracking-tight text-lg">Clinical Data Intelligence System</h1>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-xs text-right">
          <div className="font-bold">Suranjit Das</div>
          <div className="text-gray-400">AI Engineer</div>
        </div>
        <div className="w-8 h-8 rounded-full bg-dark-grey flex items-center justify-center text-white text-xs">SD</div>
      </div>
    </header>
  );
};

export default Header;
