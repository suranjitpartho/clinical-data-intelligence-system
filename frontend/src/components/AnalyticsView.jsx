import React, { useState } from 'react';
import { Activity, Clock, Zap, BarChart3, Database, Search, Brain, ChevronRight, ChevronDown } from 'lucide-react';

const AnalyticsView = ({ metrics, isLoading, onBack }) => {
  const [expandedTrace, setExpandedTrace] = useState(null);

  if (isLoading && !metrics) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-off-white h-full">
        <div className="w-12 h-12 border-2 border-gray-100 border-t-clinical-blue rounded-full animate-spin mb-4" />
        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Synchronizing Cloud Data</p>
      </div>
    );
  }

  const summary = metrics?.summary || { total_queries: 0, avg_latency: '0s', total_tokens: '0', total_cost: '$0.00' };
  const traces = metrics?.recent_traces || [];

  return (
    <div className="flex-1 bg-off-white overflow-y-auto font-sans">
      <div className="max-w-6xl mx-auto p-8">
        {/* Header Section */}
        <div className="flex justify-between items-end mb-12">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-clinical-blue animate-pulse" />
              <span className="text-[10px] font-bold text-clinical-blue uppercase tracking-widest">System Observability</span>
            </div>
            <h1 className="text-3xl font-display font-bold text-dark-grey tracking-tight">Clinical Intelligence Dashboard</h1>
            <p className="text-gray-400 text-sm mt-2">Real-time performance metrics from Langfuse Cloud</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Last Updated</p>
            <p className="text-xs font-bold text-dark-grey">{metrics?.cached_at || 'Just now'}</p>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-16">
          <StatCard 
            label="Total Clinical Queries" 
            value={summary.total_queries} 
            icon={<Activity size={20} className="text-clinical-blue" />} 
          />
          <StatCard 
            label="Avg. System Latency" 
            value={summary.avg_latency} 
            icon={<Clock size={20} className="text-clinical-blue" />} 
          />
          <StatCard 
            label="Total Token Usage" 
            value={summary.total_tokens} 
            icon={<Zap size={20} className="text-clinical-blue" />} 
          />
          <StatCard 
            label="Total API Expenditure" 
            value={summary.total_cost} 
            icon={<BarChart3 size={20} className="text-clinical-blue" />} 
          />
        </div>

        {/* Trace List */}
        <div className="space-y-4">
          <h2 className="text-xs font-bold text-gray-400 uppercase tracking-[0.2em] mb-6">Recent Clinical Executions</h2>
          
          <div className="space-y-3">
            {traces.map((trace) => {
              const isExpanded = expandedTrace === trace.id;
              return (
                <div key={trace.id} className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                  <div 
                    onClick={() => setExpandedTrace(isExpanded ? null : trace.id)}
                    className="p-5 flex items-center justify-between cursor-pointer group"
                  >
                    <div className="flex items-center gap-5 flex-1 pr-8">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors ${isExpanded ? 'bg-clinical-blue text-white' : 'bg-gray-50 text-gray-400 group-hover:bg-clinical-blue/5 group-hover:text-clinical-blue'}`}>
                        <Search size={20} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-semibold text-dark-grey leading-relaxed break-words ${!isExpanded && 'line-clamp-2'}`}>
                          {trace.input}
                        </p>
                        <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mt-1">
                          {new Date(trace.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-10 flex-shrink-0">
                      <div className="text-right">
                        <p className="text-[10px] text-gray-400 uppercase font-bold tracking-widest">Latency</p>
                        <p className="text-sm font-display font-bold text-dark-grey">{trace.total_latency}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-gray-400 uppercase font-bold tracking-widest">Tokens</p>
                        <p className="text-sm font-display font-bold text-dark-grey">{trace.total_tokens}</p>
                      </div>
                      <div className="text-right min-w-[70px]">
                        <p className="text-[10px] text-gray-400 uppercase font-bold tracking-widest">Cost</p>
                        <p className="text-sm font-display font-bold text-clinical-blue">
                          {trace.total_cost > 0 ? `$${trace.total_cost.toFixed(5)}` : '$0.00000'}
                        </p>
                      </div>
                      <div className={`transition-transform duration-300 ${isExpanded ? 'rotate-90 text-clinical-blue' : 'text-gray-300'}`}>
                        <ChevronRight size={18} />
                      </div>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="border-t border-gray-50 p-8 animate-fade-in-up">
                      <div className="text-[9px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-6">Logical Node Breakdown</div>
                      <div className="space-y-6">
                        {trace.steps.map((step, sIdx) => (
                          <div key={sIdx} className="flex items-start gap-4">
                            <div className="w-8 h-8 rounded-full bg-white border border-gray-100 flex items-center justify-center text-clinical-blue text-[10px] font-bold flex-shrink-0">
                              {step.name.charAt(0)}
                            </div>
                            <div className="flex-1">
                              <div className="flex justify-between items-center mb-2">
                                <span className="text-xs font-bold text-dark-grey uppercase tracking-wider">{step.name}</span>
                                <span className="text-[10px] font-bold text-gray-400">
                                  {step.latency} • {step.tokens} tokens • <span className="text-clinical-blue">${step.cost.toFixed(5)}</span>
                                </span>
                              </div>
                              <div className="h-1 w-full bg-gray-50 rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-clinical-blue" 
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
  <div className="bg-white p-6 rounded-xl border border-gray-100 flex flex-col gap-4">
    <div className="p-2 bg-off-white w-fit rounded-lg">{icon}</div>
    <div>
      <p className="text-2xl font-display font-bold text-dark-grey tracking-tight">{value}</p>
      <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mt-1">{label}</p>
    </div>
  </div>
);

export default AnalyticsView;
