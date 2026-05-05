import React, { useState } from 'react';
import { Activity, Clock, Zap, BarChart3 } from 'lucide-react';
import StatCard from './StatCard';
import TraceItem from './TraceItem';
import Pagination from './Pagination';

const RANGE_OPTIONS = [
  { label: '7D', value: 7 },
  { label: '15D', value: 15 },
  { label: '30D', value: 30 },
];

const AnalyticsView = ({ metrics, isLoading, onBack, range, onRangeChange, currentPage, onPageChange, pageSize }) => {
  const [expandedTrace, setExpandedTrace] = useState(null);

  if (isLoading && !metrics) {
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

  return (
    <div className="flex-1 bg-dark-bg overflow-y-auto font-sans custom-scrollbar relative">
      <div className="max-w-5xl mx-auto p-6 pb-12">

        {/* Header Row: Title LEFT | Time Range Filter RIGHT */}
        <div className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-2xl font-display font-bold text-white tracking-tight">
              LLM <span className="text-clinical-blue">Observability</span>
            </h1>
            <p className="text-gray-500 text-[11px] mt-1.5 font-medium uppercase tracking-wider">
              Inference Tracing · Token Analytics · Cost Monitoring
            </p>
          </div>

          {/* Time Range Filter — right side of header */}
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
            {/* Loading overlay — fixed to viewport center so it stays visible while scrolling */}
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
            {traces.map((trace) => (
              <TraceItem 
                key={trace.id} 
                trace={trace} 
                isExpanded={expandedTrace === trace.id}
                onToggleExpand={setExpandedTrace}
              />
            ))}
          </div>

          <Pagination 
            pagination={pagination}
            currentPage={currentPage}
            onPageChange={onPageChange}
          />
        </div>
      </div>
    </div>
  );
};


export default AnalyticsView;

