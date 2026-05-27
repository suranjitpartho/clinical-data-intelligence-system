import React, { useState } from 'react';
import { Activity, Clock, Zap, BarChart3, List, LayoutDashboard } from 'lucide-react';
import StatCard from './StatCard';
import TraceItem from './TraceItem';
import Pagination from './Pagination';
import OperationalView from './OperationalView';
import SqlSidebar from '../SqlSidebar';

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
  syncStatus,
  onSync,
  onBack, 
  range, 
  onRangeChange, 
  currentPage, 
  onPageChange, 
  pageSize 
}) => {
  const [expandedTrace, setExpandedTrace] = useState(null);
  const [isSqlOpen, setIsSqlOpen] = useState(false);
  const [selectedSql, setSelectedSql] = useState(null);

  const handleSqlView = (sql) => {
    if (isSqlOpen && selectedSql === sql) {
      setIsSqlOpen(false);
      setSelectedSql(null);
    } else {
      setSelectedSql(sql);
      setIsSqlOpen(true);
    }
  };

  const summary = metrics?.summary || { total_queries: 0, error_queries: 0, avg_latency: '0s', total_tokens: '0', total_cost: '$0.00' };
  const traces = metrics?.recent_traces || [];
  const pagination = metrics?.pagination || { current_page: 1, total_pages: 1, total_items: 0, page_size: pageSize };

  function parseLatency(s) {
    if (typeof s === 'string') return parseFloat(s.replace('s', ''));
    return s || 0;
  }
  function formatLatency(n) {
    return n.toFixed(2) + 's';
  }
  function mergeSteps(allSteps) {
    const result = [];
    for (const step of allSteps) {
      const last = result[result.length - 1];
      if (last && last.name === step.name) {
        last.latency = formatLatency(parseLatency(last.latency) + parseLatency(step.latency));
        last.tokens = (last.tokens || 0) + (step.tokens || 0);
        last.cost = (last.cost || 0) + (step.cost || 0);
      } else {
        result.push({ ...step });
      }
    }
    return result;
  }

  // Step 1: Aggregate raw traces by request_id
  const reqMap = new Map();
  for (const t of traces) {
    const rid = t.request_id;
    if (!rid) {
      continue;
    }
    if (!reqMap.has(rid)) {
      reqMap.set(rid, []);
    }
    reqMap.get(rid).push(t);
  }
  const aggregated = [];
  for (const [rid, group] of reqMap) {
    group.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    const steps = mergeSteps(group.flatMap(t => t.steps || []));
    aggregated.push({
      request_id: rid,
      session_id: group[0].session_id,
      input: group[0].input,
      output: group[group.length - 1].output,
      total_latency: formatLatency(group.reduce((s, t) => s + parseLatency(t.total_latency), 0)),
      total_tokens: group.reduce((s, t) => s + (t.total_tokens || 0), 0),
      total_cost: group.reduce((s, t) => s + (t.total_cost || 0), 0),
      status: group.some(t => t.status === 'ERROR') ? 'ERROR' : 'SUCCESS',
      error_message: group.find(t => t.error_message)?.error_message || null,
      sql_query: group.find(t => t.sql_query)?.sql_query || null,
      timestamp: group[0].timestamp,
      steps,
    });
  }
  // Traces without request_id added individually
  for (const t of traces) {
    if (!t.request_id) {
      aggregated.push({
        request_id: null,
        session_id: t.session_id,
        input: t.input,
        output: t.output,
        total_latency: t.total_latency,
        total_tokens: t.total_tokens || 0,
        total_cost: t.total_cost || 0,
        status: t.status,
        error_message: t.error_message,
        sql_query: t.sql_query,
        timestamp: t.timestamp,
        steps: t.steps || [],
      });
    }
  }

  // Step 2: Group aggregated items by session_id
  const sessionMap = new Map();
  for (const item of aggregated) {
    const sid = item.session_id;
    if (!sid) continue;
    if (!sessionMap.has(sid)) {
      sessionMap.set(sid, { session_id: sid, items: [], totalTokens: 0, totalCost: 0 });
    }
    const g = sessionMap.get(sid);
    g.items.push(item);
    g.totalTokens += (item.total_tokens || 0);
    g.totalCost += (item.total_cost || 0);
  }

  // Step 3: Build final display list
  const groupedTraces = [];
  for (const item of aggregated) {
    if (!item.session_id) {
      groupedTraces.push({ isGroup: false, request_id: item.request_id, trace: item });
    }
  }
  for (const g of sessionMap.values()) {
    if (g.items.length >= 2) {
      groupedTraces.push({
        isGroup: true,
        id: g.session_id,
        session_id: g.session_id,
        items: g.items,
        totalTokens: g.totalTokens,
        totalCost: g.totalCost,
      });
    } else {
      const item = g.items[0];
      groupedTraces.push({ isGroup: false, request_id: item.request_id, trace: item });
    }
  }
  groupedTraces.sort((a, b) => {
    const ta = a.isGroup ? a.items[0].timestamp : a.trace.timestamp;
    const tb = b.isGroup ? b.items[0].timestamp : b.trace.timestamp;
    return new Date(tb) - new Date(ta);
  });

  return (
    <div className="flex bg-dark-bg font-sans custom-scrollbar relative h-full">
      <div className="flex-1 overflow-y-auto">
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
            <div className="flex flex-col items-end gap-1.5">
              <button
                onClick={onSync}
                disabled={isSyncing}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-[9px] font-bold uppercase tracking-widest border transition-all duration-500 ${
                  isSyncing 
                    ? 'bg-white/5 text-gray-600 border-white/5 cursor-not-allowed'
                    : 'bg-white/5 text-gray-400 border-white/10 hover:border-clinical-blue/40 hover:text-clinical-blue hover:bg-white/10'
                }`}
              >
                {isSyncing ? (
                  <span className="w-3 h-3 border-2 border-white/20 border-t-clinical-blue rounded-full animate-spin" />
                ) : (
                  <Activity size={12} />
                )}
                {isSyncing ? 'Syncing...' : 'Sync Langfuse'}
              </button>
              {syncStatus === 'syncing' && (
                <span className="text-[9px] text-clinical-blue/70 font-medium tracking-wide animate-pulse">Syncing with Langfuse...</span>
              )}
              {syncStatus === 'polling' && (
                <span className="text-[9px] text-yellow-400/70 font-medium tracking-wide animate-pulse">Waiting for data...</span>
              )}
              {syncStatus && syncStatus.startsWith('polling_') && (
                <span className="text-[9px] text-yellow-400/70 font-medium tracking-wide">Retrying ({syncStatus.split('_')[1]}/12)...</span>
              )}
              {syncStatus === 'complete' && (
                <span className="text-[9px] text-green-400/80 font-medium tracking-wide transition-opacity duration-700">Sync complete</span>
              )}
              {syncStatus === 'timeout' && (
                <span className="text-[9px] text-red-400/80 font-medium tracking-wide">Sync timed out — try again</span>
              )}
            </div>
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
                {groupedTraces.map((entry) => {
                  if (!entry.isGroup) {
                    const rid = entry.request_id;
                    return (
                      <TraceItem 
                        key={rid || entry.trace.timestamp} 
                        trace={entry.trace} 
                        isExpanded={expandedTrace === rid}
                        onToggleExpand={() => setExpandedTrace(prev => prev === rid ? null : rid)}
                        onSqlView={handleSqlView}
                        isSqlOpen={isSqlOpen}
                        selectedSql={selectedSql}
                      />
                    );
                  }

                  return (
                    <div key={entry.id} className="rounded-xl border border-white/10 bg-[#0A0F1C]/40 overflow-hidden relative shadow-[0_4px_20px_rgba(0,0,0,0.2)]">
                      <div className="px-5 py-3 flex justify-between items-center border-b border-white/5 bg-gradient-to-r from-white/[0.03] to-transparent">
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Session:</span>
                          <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest bg-white/5 px-1.5 py-0.5 rounded border border-white/5">{entry.session_id.slice(-8)}</span>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: '#9CA3AF' }}>{entry.totalTokens} Tokens</span>
                          <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: '#9CA3AF' }}>${entry.totalCost.toFixed(5)}</span>
                        </div>
                      </div>
                      <div className="p-4 space-y-3 bg-[#0F172A]/20">
                        {entry.items.map(item => (
                          <TraceItem 
                            key={item.request_id} 
                            trace={item} 
                            isExpanded={expandedTrace === item.request_id}
                            onToggleExpand={() => setExpandedTrace(prev => prev === item.request_id ? null : item.request_id)}
                            onSqlView={handleSqlView}
                            isSqlOpen={isSqlOpen}
                            selectedSql={selectedSql}
                          />
                        ))}
                      </div>
                    </div>
                  );
                })}

              <Pagination 
                pagination={pagination}
                currentPage={currentPage}
                onPageChange={onPageChange}
              />
            </div>
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

      <SqlSidebar
        isOpen={isSqlOpen}
        setIsOpen={setIsSqlOpen}
        sql={selectedSql}
      />
    </div>
  );
};

export default AnalyticsView;

