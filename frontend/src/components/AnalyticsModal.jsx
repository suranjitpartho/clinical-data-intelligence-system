import React from 'react';
import { X, Activity, Cpu, ShieldCheck, Zap, BarChart3 } from 'lucide-react';

const AnalyticsModal = ({ isOpen, onClose, metrics }) => {
  if (!isOpen) return null;

  const { summary, distribution } = metrics || {
    summary: { total_queries: 0, success_rate: '0%', avg_latency: '0s', total_tokens: '0', roi_estimate: '$0' },
    distribution: { sql: 0, rag: 0, other: 0 }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 animate-fade-in">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-dark-grey/40 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden animate-scale-in border border-gray-100">
        {/* Header */}
        <div className="bg-dark-grey p-6 flex justify-between items-center">
          <div className="flex items-center gap-3 text-white">
            <Activity className="text-blue-400" size={20} />
            <div>
              <h2 className="text-lg font-bold tracking-tight">System Performance Monitor</h2>
              <p className="text-[10px] text-gray-400 uppercase tracking-widest font-medium">Real-time Observability Metrics</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full text-gray-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-8 space-y-8">
          {/* Main Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard 
              label="Total Consultations" 
              value={summary.total_queries} 
              icon={<Zap size={14} />} 
              color="text-blue-500" 
            />
            <MetricCard 
              label="Success Rate" 
              value={summary.success_rate} 
              icon={<ShieldCheck size={14} />} 
              color="text-emerald-500" 
            />
            <MetricCard 
              label="Avg. Latency" 
              value={summary.avg_latency} 
              icon={<Cpu size={14} />} 
              color="text-orange-500" 
            />
            <MetricCard 
              label="Total Tokens" 
              value={summary.total_tokens} 
              icon={<BarChart3 size={14} />} 
              color="text-purple-500" 
            />
          </div>

          {/* Distribution Section */}
          <div className="bg-gray-50 rounded-xl p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest">Engine Distribution</h3>
              <span className="text-[10px] text-gray-400 font-medium bg-white px-2 py-1 rounded-full border border-gray-100">Last 7 Days</span>
            </div>
            
            <div className="space-y-4">
              <ProgressBar label="SQL Reasoning Engine" count={distribution.sql} total={summary.total_queries} color="bg-blue-500" />
              <ProgressBar label="Protocol RAG Engine" count={distribution.rag} total={summary.total_queries} color="bg-orange-500" />
              <ProgressBar label="Direct Synthesis" count={distribution.other} total={summary.total_queries} color="bg-gray-300" />
            </div>
          </div>

          {/* ROI Banner */}
          <div className="flex items-center gap-4 p-4 bg-emerald-50 rounded-lg border border-emerald-100">
            <div className="p-2 bg-white rounded-md shadow-sm">
              <Zap className="text-emerald-500" size={16} />
            </div>
            <div>
              <p className="text-[11px] text-emerald-800 font-bold uppercase tracking-tight">Estimated ROI</p>
              <p className="text-sm text-emerald-600 font-medium">This system has saved approximately <span className="font-bold underline decoration-emerald-300 decoration-2">{summary.roi_estimate}</span> in manual clinical data processing costs.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const MetricCard = ({ label, value, icon, color }) => (
  <div className="p-4 bg-white border border-gray-100 rounded-xl shadow-sm flex flex-col gap-2">
    <div className={`flex items-center gap-2 ${color} font-bold`}>
      {icon}
      <span className="text-[10px] uppercase tracking-tighter">{label}</span>
    </div>
    <div className="text-xl font-bold text-dark-grey tracking-tight">{value}</div>
  </div>
);

const ProgressBar = ({ label, count, total, color }) => {
  const percentage = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-[11px] font-medium">
        <span className="text-gray-600">{label}</span>
        <span className="text-dark-grey font-bold">{count} ({Math.round(percentage)}%)</span>
      </div>
      <div className="h-2 w-full bg-white rounded-full overflow-hidden border border-gray-100">
        <div 
          className={`h-full ${color} transition-all duration-1000 ease-out`} 
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export default AnalyticsModal;
