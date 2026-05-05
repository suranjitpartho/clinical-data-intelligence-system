import React from 'react';

const StatCard = ({ label, value, icon }) => (
  <div className="bg-slate-900/60 backdrop-blur-md p-5 rounded-md border border-white/10 hover:border-white/20 transition-all duration-300 group">
    <div className="p-2 bg-white/5 w-fit rounded-md mb-4 group-hover:bg-clinical-blue/10 transition-colors border border-white/5">{icon}</div>
    <div>
      <p className="text-xl font-display font-bold text-white tracking-tight group-hover:text-clinical-blue transition-colors">{value}</p>
      <p className="text-[9px] text-gray-500 font-bold uppercase tracking-[0.2em] mt-1.5">{label}</p>
    </div>
  </div>
);

export default StatCard;
