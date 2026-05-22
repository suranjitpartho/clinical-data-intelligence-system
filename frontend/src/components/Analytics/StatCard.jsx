import React from 'react';

const StatCard = ({ 
  label, 
  value, 
  suffix,
  icon, 
  iconColor = '#06B6D4', 
  footerLeft, 
  footerRight,
  footerRightColor
}) => (
  <div className="bg-slate-900/60 backdrop-blur-md p-4 rounded-md border border-white/10 flex flex-col justify-between h-full hover:border-white/20 transition-all duration-300">
    <div>
      {/* Header Row */}
      <div className="flex items-center gap-2 mb-4">
        <span style={{ color: iconColor }}>{icon}</span>
        <h3 className="text-[9px] font-bold text-gray-500 uppercase tracking-[0.2em]">{label}</h3>
      </div>
      
      {/* Value Row */}
      <div>
        <span className="text-xl font-display font-bold text-white tracking-tight">
          {value}
        </span>
        {suffix && (
          <span className="text-[9px] font-bold text-gray-500 ml-1.5 uppercase tracking-widest">
            {suffix}
          </span>
        )}
      </div>
    </div>

    {/* Footer Row */}
    {(footerLeft || footerRight) && (
      <div className="mt-3 pt-3 border-t border-white/5 flex justify-between text-[8px] font-bold uppercase tracking-widest">
        {footerLeft && <span className="text-gray-500">{footerLeft}</span>}
        {footerRight && <span style={{ color: footerRightColor || iconColor }}>{footerRight}</span>}
      </div>
    )}
  </div>
);

export default StatCard;
