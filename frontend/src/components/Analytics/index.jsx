import React, { useState } from 'react';
import { Activity, Clock, Zap, BarChart3, List, LayoutDashboard } from 'lucide-react';
import StatCard from './StatCard';
import TraceItem from './TraceItem';
import Pagination from './Pagination';
import OperationalView from './OperationalView';

const RANGE_OPTIONS = [
  { label: '7D', value: 7 },
  { label: '15D', value: 15 },
  { label: '30D', value: 30 },
];

const AnalyticsView = ({ 
  metrics, 
  operationalData,
  subView,
  setSubView,
  isLoading, 
  onBack, 
  range, 
  onRangeChange, 
  currentPage, 
  onPageChange, 
  pageSize 
}) => {
  const [expandedTrace, setExpandedTrace] = useState(null);

  if (isLoading && !metrics && !operationalData) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-dark-bg h-full">
        <div className="w-12 h-12 border-2 border-white/5 border-t-clinical-blue rounded-full animate-spin mb-4" />
        <p className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.3em]">Synchronizing Intelligence Nodes</p>
      </div>
    );
  }

  const summary = metrics?.summary || { total_queries: 0, avg_latency: '0s', total_tokens: '0', total_cost: '$0.00' };
  const traces = metrics?.recent_traces || [];
  const pagination = metrics?.pagination || { current_page: 1, total_pages: 1, total_items: 0, page_size: pageSize };
  const groupedTraces = [];
  const sessionMap = new Map();

  traces.forEach(trace => {
    if (!trace.session_id) {
      groupedTraces.push({ isGroup: false, id: trace.id, trace });
    } else {
      if (sessionMap.has(trace.session_id)) {
        sessionMap.get(trace.session_id).traces.push(trace);
        sessionMap.get(trace.session_id).totalCost += trace.total_cost;
        sessionMap.get(trace.session_id).totalTokens += trace.total_tokens;
      } else {
        const group = { isGroup: true, id: trace.session_id, session_id: trace.session_id, traces: [trace], totalCost: trace.total_cost, totalTokens: trace.total_tokens };
        sessionMap.set(trace.session_id, group);
        groupedTraces.push(group);
      }
    }
  });

  return (
    <div className="flex-1 bg-dark-bg overflow-y-auto font-sans custom-scrollbar relative">
      <div className="max-w-5xl mx-auto p-6 pb-12">

        {/* Header Row: Title LEFT | SubView Toggle CENTER | Time Range Filter RIGHT */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
          <div>
            <h1 className="text-2xl font-display font-bold text-white tracking-tight">
              LLM <span className="text-clinical-blue">Observability</span>
            </h1>
            <p className="text-gray-500 text-[11px] mt-1.5 font-medium uppercase tracking-wider">
              {subView === 'traces' ? 'Inference Tracing & Execution' : 'Operational Trends & Model Performance'}
            </p>
          </div>

          {/* SubView Toggle */}
          <div className="flex bg-white/5 p-1 rounded-xl border border-white/10">
            <button
              onClick={() => setSubView('traces')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all duration-300 ${
                subView === 'traces' 
                  ? 'bg-clinical-blue text-slate-900 shadow-lg' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <List size={14} />
              Traces
            </button>
            <button
              onClick={() => setSubView('operational')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all duration-300 ${
                subView === 'operational' 
                  ? 'bg-clinical-blue text-slate-900 shadow-lg' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <LayoutDashboard size={14} />
              Operations
            </button>
          </div>

          {/* Time Range Filter */}
          <div className="flex items-center gap-2">
            <span className="text-[9px] font-bold text-gray-600 uppercase tracking-[0.2em] mr-1">Window</span>
            {RANGE_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => onRangeChange(opt.value)}
                className={`px-3.5 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-widest border transition-all duration-200 ${
                  range === opt.value
                    ? 'bg-clinical-blue text-slate-900 border-clinical-blue shadow-[0_0_12px_rgba(0,200,255,0.25)]'
                    : 'bg-white/5 text-gray-400 border-white/10 hover:border-clinical-blue/40 hover:text-clinical-blue'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {subView === 'traces' ? (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-10">
              <StatCard label="Inference Queries" value={summary.total_queries} icon={<Activity size={16} className="text-clinical-blue" />} />
              <StatCard label="Agent Latency"     value={summary.avg_latency}   icon={<Clock    size={16} className="text-clinical-blue" />} />
              <StatCard label="Token Usage"       value={summary.total_tokens}  icon={<Zap      size={16} className="text-clinical-blue" />} />
              <StatCard label="Compute Expense"   value={summary.total_cost}    icon={<BarChart3 size={16} className="text-clinical-blue" />} />
            </div>

            {/* Trace List */}
            <div className="space-y-6">
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2.5">
                <div className="flex items-center gap-3">
                  <h2 className="text-[10px] font-bold text-gray-600 uppercase tracking-[0.3em]">Inference Traces</h2>
                  <span className="text-[9px] text-gray-600 font-bold">
                    {pagination.total_items} total · Page {pagination.current_page} of {pagination.total_pages}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {isLoading ? (
                    <>
                      <div className="w-3 h-3 border border-white/10 border-t-clinical-blue rounded-full animate-spin" />
                      <span className="text-[9px] text-clinical-blue font-bold tracking-widest uppercase">Updating...</span>
                    </>
                  ) : (
                    <>
                      <div className="w-1.5 h-1.5 rounded-full bg-clinical-blue animate-pulse" />
                      <span className="text-[9px] text-gray-500 font-bold tracking-widest uppercase">
                        Synced {metrics?.cached_at || '—'}
                      </span>
                    </>
                  )}
                </div>
              </div>

              <div className="relative space-y-4">
                {isLoading && traces.length > 0 && (
                  <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/50 backdrop-blur-sm pointer-events-none">
                    <div className="flex flex-col items-center gap-3">
                      <div className="w-8 h-8 border-2 border-white/5 border-t-clinical-blue rounded-full animate-spin" />
                      <p className="text-[10px] font-bold text-gray-300 uppercase tracking-[0.25em]">Fetching Traces</p>
                    </div>
                  </div>
                )}
                {traces.length === 0 && !isLoading && (
                  <div className="text-center py-16 text-gray-600 text-[11px] font-bold uppercase tracking-widest">
                    No traces found for the selected time window.
                  </div>
                )}
                {groupedTraces.map((group) => {
                  if (!group.isGroup || group.traces.length === 1) {
                    const trace = group.isGroup ? group.traces[0] : group.trace;
                    return (
                      <TraceItem 
                        key={trace.id} 
                        trace={trace} 
                        isExpanded={expandedTrace === trace.id}
                        onToggleExpand={setExpandedTrace}
                      />
                    );
                  }

                  return (
                    <div key={group.id} className="rounded-xl border border-white/10 bg-[#0A0F1C]/40 overflow-hidden relative shadow-[0_4px_20px_rgba(0,0,0,0.2)]">
                      <div className="px-5 py-3 flex justify-between items-center border-b border-white/5 bg-gradient-to-r from-white/[0.03] to-transparent">
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Session:</span>
                          <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest bg-white/5 px-1.5 py-0.5 rounded border border-white/5">{group.session_id.slice(-8)}</span>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">{group.totalTokens} Tokens</span>
                          <span className="text-[10px] font-bold text-clinical-blue uppercase tracking-widest">${group.totalCost.toFixed(5)}</span>
                        </div>
                      </div>
                      <div className="p-4 space-y-3 bg-[#0F172A]/20">
                        {group.traces.map(trace => (
                          <TraceItem 
                            key={trace.id} 
                            trace={trace} 
                            isExpanded={expandedTrace === trace.id}
                            onToggleExpand={setExpandedTrace}
                          />
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>

              <Pagination 
                pagination={pagination}
                currentPage={currentPage}
                onPageChange={onPageChange}
              />
            </div>
          </>
        ) : (
          <OperationalView 
            data={operationalData} 
            isLoading={isLoading} 
            days_back={range}
          />
        )}
      </div>
    </div>
  );
};

export default AnalyticsView;

