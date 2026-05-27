import React from 'react';
import { Search, ChevronRight, Database, AlertTriangle, Terminal } from 'lucide-react';
const TraceItem = ({ trace, isExpanded, onToggleExpand, onSqlView, isSqlOpen, selectedSql }) => {
  const isError = trace.status === 'ERROR';

  return (
    <div className={`bg-[#0F172A]/80 backdrop-blur-md rounded-lg border transition-all duration-300 overflow-hidden ${
      isExpanded ? 'border-clinical-blue/40' : 'border-white/10 hover:border-white/20'
    }`}>
      <div
        onClick={() => onToggleExpand(isExpanded ? null : trace.id)}
        className="p-4 flex items-start justify-between cursor-pointer group"
      >
        <div className="flex items-start gap-4 flex-1 pr-6 pt-0.5">
          <div className={`w-10 h-10 rounded-md flex items-center justify-center transition-all duration-300 ${isExpanded ? 'bg-clinical-blue text-slate-900' : 'bg-white/5 text-gray-500 group-hover:bg-white/10 group-hover:text-clinical-blue'}`}>
            <Search size={18} />
          </div>
          <div className="flex-1 min-w-0">
            <p className={`text-[13px] font-semibold text-gray-200 leading-relaxed break-words ${!isExpanded && 'line-clamp-1'}`}>
              {trace.input}
            </p>
            <div className="flex items-center gap-3 mt-1.5">
              <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">
                {new Date(trace.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
              </p>
              <span className="w-1 h-1 bg-gray-700 rounded-full"></span>
              <span className="text-[10px] font-bold text-gray-600 uppercase tracking-widest">ID: {trace.request_id ? trace.request_id.slice(-8) : '---'}</span>
              {isError && (
                <span className="flex items-center gap-1 text-[9px] font-bold px-1.5 py-0.5 rounded border"
                  style={{ color: '#F87171', borderColor: 'rgba(248, 113, 113, 0.3)', backgroundColor: 'rgba(248, 113, 113, 0.08)' }}>
                  <AlertTriangle size={9} />
                  ERROR
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-start gap-8 flex-shrink-0 pt-1.5">
          <div className="text-right">
            <p className="text-[8px] text-gray-600 uppercase font-bold tracking-widest mb-0.5">Latency</p>
            <p className="text-xs font-display font-bold text-gray-300">{trace.total_latency}</p>
          </div>
          <div className="text-right">
            <p className="text-[8px] text-gray-600 uppercase font-bold tracking-widest mb-0.5">Tokens</p>
            <p className="text-xs font-display font-bold" style={{ color: '#06B6D4' }}>{trace.total_tokens}</p>
          </div>
          <div className="text-right min-w-[70px]">
            <p className="text-[8px] text-gray-600 uppercase font-bold tracking-widest mb-0.5">Cost</p>
            <p className="text-xs font-display font-bold" style={{ color: '#9AED1F' }}>
              {trace.total_cost > 0 ? `$${trace.total_cost.toFixed(5)}` : '$0.00000'}
            </p>
          </div>
          <div className={`transition-all duration-500 pt-1 ${isExpanded ? 'rotate-90 text-clinical-blue translate-x-1' : 'text-gray-700 group-hover:text-gray-400'}`}>
            <ChevronRight size={16} />
          </div>
        </div>
      </div>

      {isExpanded && (
        <div className="border-t border-white/5 bg-black/20 p-6 animate-fade-in-up">
          <div className="flex items-center gap-3 mb-5">
            <Database size={14} className="text-gray-500" />
            <div className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.3em]">Logical Execution Flow</div>
            {trace.sql_query && onSqlView && (
              <button
                onClick={(e) => { e.stopPropagation(); onSqlView(trace.sql_query); }}
                className={`ml-auto flex items-center gap-2 border px-3 py-1 rounded-md transition-all cursor-pointer shadow-sm ${
                  isSqlOpen && selectedSql === trace.sql_query
                    ? 'bg-clinical-blue/20 border-clinical-blue text-clinical-blue'
                    : 'bg-white/[0.05] border-white/10 hover:bg-white/[0.08] text-gray-300'
                }`}
              >
                <Terminal size={12} className={isSqlOpen && selectedSql === trace.sql_query ? 'text-clinical-blue' : 'text-gray-400'} />
                <span className="text-[9px] font-bold uppercase tracking-wider">SQL</span>
              </button>
            )}
          </div>
          <div className="space-y-5">
            {trace.steps.map((step, sIdx) => (
              <div key={sIdx} className="flex items-start gap-5 relative">
                {sIdx !== trace.steps.length - 1 && (
                  <div className="absolute left-3.5 top-7 bottom-[-10px] w-[1px] bg-white/5"></div>
                )}
                <div className="w-7 h-7 rounded-md bg-slate-800 border border-white/10 flex items-center justify-center text-clinical-blue text-[10px] font-bold flex-shrink-0 z-10">
                  {step.name.charAt(0)}
                </div>
                <div className="flex-1 pt-0">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[12px] font-bold text-gray-200 uppercase tracking-wider">{step.name}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded border" style={{ color: '#9CA3AF', borderColor: 'rgba(255, 255, 255, 0.05)', backgroundColor: 'rgba(255, 255, 255, 0.02)' }}>
                        {step.latency}
                      </span>
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded border" style={{ color: '#06B6D4', borderColor: 'rgba(6, 182, 212, 0.2)', backgroundColor: 'rgba(6, 182, 212, 0.05)' }}>
                        {step.tokens} TOKENS
                      </span>
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded border" style={{ color: '#9AED1F', borderColor: 'rgba(154, 237, 31, 0.2)', backgroundColor: 'rgba(154, 237, 31, 0.05)' }}>
                        ${step.cost.toFixed(5)}
                      </span>
                    </div>
                  </div>
                  <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden shadow-inner">
                    <div
                      className="h-full bg-clinical-blue transition-all duration-1000"
                      style={{ width: `${Math.min(100, (parseFloat(step.latency) / parseFloat(trace.total_latency)) * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TraceItem;
