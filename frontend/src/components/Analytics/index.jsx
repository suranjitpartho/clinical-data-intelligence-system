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
  isSyncing,
  onSync,
  onBack, 
  range, 
  onRangeChange, 
  currentPage, 
  onPageChange, 
  pageSize 
}) => {
  const [expandedTrace, setExpandedTrace] = useState(null);

  const summary = metrics?.summary || { total_queries: 0, error_queries: 0, avg_latency: '0s', total_tokens: '0', total_cost: '$0.00' };
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

        {/* Header Section: Static 2-Row Layout to prevent flickering */}
        <div className="mb-10">
          {/* Row 1: Identity */}
          <div className="mb-6 flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-display font-normal text-white tracking-tight">
                LLM Observability
              </h1>
              <p className="text-gray-500 text-[10px] mt-1 font-bold uppercase tracking-[0.2em]">
                Inference Tracing & Operational Performance
              </p>
            </div>
            <button
              onClick={onSync}
              disabled={isSyncing}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-[9px] font-bold uppercase tracking-widest border transition-all duration-500 ${
                isSyncing 
                  ? 'bg-white/5 text-gray-600 border-white/5 cursor-not-allowed'
                  : 'bg-white/5 text-gray-400 border-white/10 hover:border-clinical-blue/40 hover:text-clinical-blue hover:bg-white/10'
              }`}
            >
              <Activity size={12} className={isSyncing ? 'animate-spin' : ''} />
              {isSyncing ? 'Syncing...' : 'Sync Langfuse'}
            </button>
          </div>

          {/* Row 2: Control Strip (Compact & Unified) */}
          <div className="flex flex-wrap items-center gap-4 bg-white/[0.02] p-2 rounded-2xl border border-white/5">
            {/* View Switcher */}
            <div className="flex bg-black/20 p-1 rounded-xl border border-white/5">
              <button
                onClick={() => setSubView('traces')}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-widest ${
                  subView === 'traces' 
                    ? 'bg-white/10 text-clinical-blue border border-white/10 shadow-lg' 
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                <List size={14} />
                Traces
              </button>
              <button
                onClick={() => setSubView('operational')}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-widest ${
                  subView === 'operational' 
                    ? 'bg-white/10 text-clinical-blue border border-white/10 shadow-lg' 
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                <LayoutDashboard size={14} />
                Operations
              </button>
            </div>

            <div className="ml-auto flex items-center gap-2">
              <span className="text-[9px] font-bold text-gray-600 uppercase tracking-[0.2em] mr-2">Range</span>
              <div className="flex gap-1.5">
                {RANGE_OPTIONS.map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => onRangeChange(opt.value)}
                    className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-widest border transition-all duration-200 ${
                      range === opt.value
                        ? 'bg-white/10 text-clinical-blue border-clinical-blue/40 shadow-[0_0_15px_rgba(0,200,255,0.1)]'
                        : 'bg-white/5 text-gray-500 border-white/5 hover:border-white/20 hover:text-gray-300'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {subView === 'traces' ? (
          <>
             {/* Stats Grid */}
             <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-10">
               <StatCard 
                 label="Inference Queries" 
                 value={summary.total_queries} 
                 suffix="Queries"
                 icon={<Activity size={16} />} 
                 iconColor="#06B6D4" 
                 footerLeft="Failed Traces"
                 footerRight={`${summary.error_queries || 0} Error${(summary.error_queries || 0) === 1 ? '' : 's'}`}
                 footerRightColor={(summary.error_queries || 0) > 0 ? '#F87171' : '#06B6D4'}
               />
               <StatCard 
                 label="Agent Latency" 
                 value={summary.avg_latency} 
                 icon={<Clock size={16} />} 
                 iconColor="#06B6D4" 
                 footerLeft="Metric Type"
                 footerRight="Success Avg"
               />
               <StatCard 
                 label="Token Usage" 
                 value={summary.total_tokens} 
                 suffix="Tokens"
                 icon={<Zap size={16} />} 
                 iconColor="#06B6D4" 
                 footerLeft="Calculation"
                 footerRight="Cumulative"
               />
               <StatCard 
                 label="Compute Expense" 
                 value={summary.total_cost} 
                 suffix="USD"
                 icon={<BarChart3 size={16} />} 
                 iconColor="#9AED1F" 
                 footerLeft="Calculated"
                 footerRight="Live Cache"
               />
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
                  <div className="w-1.5 h-1.5 rounded-full bg-clinical-blue animate-pulse" />
                  <span className="text-[9px] text-gray-500 font-bold tracking-widest uppercase">
                    Synced {metrics?.cached_at || '—'}
                  </span>
                </div>
              </div>

              <div className="relative space-y-4">
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
                          <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: '#9CA3AF' }}>{group.totalTokens} Tokens</span>
                          <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: '#9CA3AF' }}>${group.totalCost.toFixed(5)}</span>
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

