import React, { useState } from 'react';
import { Activity, Clock, Zap, BarChart3, Database, Search, Brain, ChevronRight, ChevronDown } from 'lucide-react';

const AnalyticsView = ({ metrics, isLoading, onBack }) => {
  const [expandedTrace, setExpandedTrace] = useState(null);

  if (isLoading && !metrics) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-dark-bg h-full">
        <div className="w-12 h-12 border-2 border-white/5 border-t-clinical-blue rounded-full animate-spin mb-4 shadow-[0_0_15px_rgba(34,211,238,0.2)]" />
        <p className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.3em]">Synchronizing Intelligence Nodes</p>
      </div>
    );
  }

  const summary = metrics?.summary || { total_queries: 0, avg_latency: '0s', total_tokens: '0', total_cost: '$0.00' };
  const traces = metrics?.recent_traces || [];

  return (
    <div className="flex-1 bg-dark-bg overflow-y-auto font-sans custom-scrollbar relative">
      <div className="max-w-5xl mx-auto p-6 pb-12">
        {/* Header Section */}
        <div className="flex justify-between items-end mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-1.5 h-1.5 rounded-full bg-clinical-blue shadow-[0_0_8px_rgba(34,211,238,0.8)] animate-pulse" />
              <span className="text-[9px] font-bold text-clinical-blue uppercase tracking-[0.2em]">Agent Intelligence Node</span>
            </div>
            <h1 className="text-2xl font-display font-bold text-white tracking-tight">Agent <span className="text-clinical-blue">Performance</span></h1>

            <p className="text-gray-500 text-[11px] mt-1.5 font-medium uppercase tracking-wider">Telemetry & Resource Optimization</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5 px-1">Last Synced</p>
            <div className="bg-white/5 px-4 py-1.5 rounded-full border border-white/5 inline-block">
              <p className="text-xs font-bold text-gray-300">{metrics?.cached_at || 'Just now'}</p>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-10">
          <StatCard 
            label="Inference Queries" 
            value={summary.total_queries} 
            icon={<Activity size={16} className="text-clinical-blue" />} 
          />
          <StatCard 
            label="Agent Latency" 
            value={summary.avg_latency} 
            icon={<Clock size={16} className="text-clinical-blue" />} 
          />
          <StatCard 
            label="Token Usage" 
            value={summary.total_tokens} 
            icon={<Zap size={16} className="text-clinical-blue" />} 
          />
          <StatCard 
            label="Compute Expense" 
            value={summary.total_cost} 
            icon={<BarChart3 size={16} className="text-clinical-blue" />} 
          />
        </div>

        {/* Trace List */}
        <div className="space-y-6">
          <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2.5">
            <h2 className="text-[10px] font-bold text-gray-600 uppercase tracking-[0.3em]">Agent Execution Logs</h2>
            <span className="text-[9px] bg-clinical-blue/10 text-clinical-blue px-2 py-0.5 rounded-full font-bold border border-clinical-blue/20">REAL-TIME</span>
          </div>
          
          <div className="space-y-4">
            {traces.map((trace) => {
              const isExpanded = expandedTrace === trace.id;
              return (
                <div key={trace.id} className={`bg-[#0F172A]/80 backdrop-blur-md rounded-2xl border transition-all duration-300 overflow-hidden ${isExpanded ? 'border-clinical-blue/40 shadow-[0_0_30px_rgba(34,211,238,0.1)]' : 'border-white/10 hover:border-white/20'}`}>
                  <div 
                    onClick={() => setExpandedTrace(isExpanded ? null : trace.id)}
                    className="p-4 flex items-start justify-between cursor-pointer group"
                  >
                    <div className="flex items-start gap-4 flex-1 pr-6 pt-0.5">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-300 ${isExpanded ? 'bg-clinical-blue text-slate-900 shadow-[0_0_12px_rgba(34,211,238,0.4)]' : 'bg-white/5 text-gray-500 group-hover:bg-white/10 group-hover:text-clinical-blue'}`}>
                        <Search size={18} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-[13px] font-semibold text-gray-200 leading-relaxed break-words ${!isExpanded && 'line-clamp-1'}`}>
                          {trace.input}
                        </p>
                        <div className="flex items-center gap-3 mt-1.5">
                          <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">
                            {new Date(trace.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                          </p>
                          <span className="w-1 h-1 bg-gray-700 rounded-full"></span>
                          <span className="text-[10px] font-bold text-gray-600 uppercase tracking-widest">ID: {trace.id.slice(-8)}</span>
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
                        <p className="text-xs font-display font-bold text-gray-300">{trace.total_tokens}</p>
                      </div>
                      <div className="text-right min-w-[70px]">
                        <p className="text-[8px] text-gray-600 uppercase font-bold tracking-widest mb-0.5">Cost</p>
                        <p className="text-xs font-display font-bold text-clinical-blue">
                          {trace.total_cost > 0 ? `$${trace.total_cost.toFixed(5)}` : '$0.00000'}
                        </p>
                      </div>
                      <div className={`transition-all duration-500 pt-1 ${isExpanded ? 'rotate-90 text-clinical-blue translate-x-1' : 'text-gray-700 group-hover:text-gray-400'}`}>
                        <ChevronRight size={16} />
                      </div>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="border-t border-white/5 bg-black/20 p-10 animate-fade-in-up">
                      <div className="flex items-center gap-3 mb-8">
                         <Database size={14} className="text-gray-500" />
                         <div className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.3em]">Logical Execution Flow</div>
                      </div>
                      <div className="space-y-8">
                        {trace.steps.map((step, sIdx) => (
                          <div key={sIdx} className="flex items-start gap-6 relative">
                            {sIdx !== trace.steps.length - 1 && (
                              <div className="absolute left-5 top-10 bottom-[-20px] w-[1px] bg-white/5"></div>
                            )}
                            <div className="w-10 h-10 rounded-xl bg-slate-800 border border-white/10 flex items-center justify-center text-clinical-blue text-xs font-bold flex-shrink-0 z-10 shadow-lg">
                              {step.name.charAt(0)}
                            </div>
                            <div className="flex-1 pt-1">
                              <div className="flex justify-between items-center mb-3">
                                <span className="text-[13px] font-bold text-gray-200 uppercase tracking-wider">{step.name}</span>
                                <div className="flex items-center gap-4">
                                  <span className="text-[10px] font-bold text-gray-500 bg-white/5 px-2 py-0.5 rounded border border-white/5">
                                    {step.latency}
                                  </span>
                                  <span className="text-[10px] font-bold text-gray-500 bg-white/5 px-2 py-0.5 rounded border border-white/5">
                                    {step.tokens} TOKENS
                                  </span>
                                  <span className="text-[10px] font-bold text-clinical-blue bg-clinical-blue/5 px-2 py-0.5 rounded border border-clinical-blue/10">
                                    ${step.cost.toFixed(5)}
                                  </span>
                                </div>
                              </div>
                              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden shadow-inner">
                                <div 
                                  className="h-full bg-clinical-blue shadow-[0_0_10px_rgba(34,211,238,0.5)] transition-all duration-1000" 
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
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ label, value, icon }) => (
  <div className="bg-slate-900/60 backdrop-blur-md p-5 rounded-xl border border-white/10 hover:border-white/20 transition-all duration-300 group shadow-lg">
    <div className="p-2 bg-white/5 w-fit rounded-lg mb-4 group-hover:bg-clinical-blue/10 transition-colors border border-white/5">{icon}</div>
    <div>
      <p className="text-xl font-display font-bold text-white tracking-tight group-hover:text-clinical-blue transition-colors">{value}</p>
      <p className="text-[9px] text-gray-500 font-bold uppercase tracking-[0.2em] mt-1.5">{label}</p>
    </div>
  </div>
);


export default AnalyticsView;
