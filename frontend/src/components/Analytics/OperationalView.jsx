import React, { useMemo } from 'react';
import { Activity, Zap, Award, Clock, TrendingUp } from 'lucide-react';

// --- Easy Chart Config ---
const CHART_TENSION = 0.2; // Increase for smoother curves, decrease for straighter lines

const getSmoothPath = (pointsStr, tension = CHART_TENSION) => {
  if (!pointsStr) return "";
  const pts = pointsStr.split(' ').map(p => {
    const [x, y] = p.split(',').map(Number);
    return { x, y };
  });
  if (pts.length < 2) return "";
  
  let d = `M ${pts[0].x},${pts[0].y}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const curr = pts[i];
    const next = pts[i + 1];
    const offset = (next.x - curr.x) * tension;
    d += ` C ${curr.x + offset},${curr.y} ${next.x - offset},${next.y} ${next.x},${next.y}`;
  }
  return d;
};

const OperationalView = ({ data, isLoading, days_back }) => {
  if (!data || data.error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[400px] border border-red-500/20 bg-red-500/5 rounded-2xl p-8">
        <p className="text-red-400 text-[11px] font-bold uppercase tracking-[0.2em] mb-2">Operational Pipeline Failure</p>
        <p className="text-gray-500 text-[10px] uppercase tracking-widest max-w-md text-center leading-relaxed">
          {data?.error || "No data received from the intelligence service. Verify connectivity to Langfuse."}
        </p>
      </div>
    );
  }

  const { daily_trends = [], heatmap_data = [], comparison = [], best_value = "Pending" } = data;

  const trendData = useMemo(() => {
    if (daily_trends.length < 2) return null;
    const maxTokens = Math.max(...daily_trends.map(d => Number(d.sum_totalTokens) || 0), 1);
    const maxCost = Math.max(...daily_trends.map(d => Number(d.sum_totalCost) || 0), 0.01);
    const width = 800;
    const height = 150;

    const tokenPoints = daily_trends.map((d, i) => {
      const x = (i / (daily_trends.length - 1)) * width;
      const y = height - ((Number(d.sum_totalTokens) || 0) / maxTokens) * height;
      return `${x},${y}`;
    }).join(' ');

    const costPoints = daily_trends.map((d, i) => {
      const x = (i / (daily_trends.length - 1)) * width;
      const y = height - ((Number(d.sum_totalCost) || 0) / maxCost) * height;
      return `${x},${y}`;
    }).join(' ');

    const maxTokensIdx = daily_trends.findIndex(d => (Number(d.sum_totalTokens) || 0) === maxTokens);
    const maxCostIdx = daily_trends.findIndex(d => (Number(d.sum_totalCost) || 0) === maxCost);

    const tokenPeakCoord = {
      x: (maxTokensIdx / (daily_trends.length - 1)) * width,
      y: height - ((Number(daily_trends[maxTokensIdx]?.sum_totalTokens) || 0) / maxTokens) * height
    };

    const costPeakCoord = {
      x: (maxCostIdx / (daily_trends.length - 1)) * width,
      y: height - ((Number(daily_trends[maxCostIdx]?.sum_totalCost) || 0) / maxCost) * height
    };

    return { tokenPoints, costPoints, width, height, maxTokens, maxCost, tokenPeakCoord, costPeakCoord };
  }, [daily_trends]);

  const heatmapMatrix = useMemo(() => {
    const matrix = Array(7).fill(0).map(() => Array(24).fill(null));
    heatmap_data.forEach(d => {
      const date = new Date(d.time_dimension);
      if (isNaN(date.getTime())) return;
      const day = date.getDay();
      const hour = date.getHours();
      matrix[day][hour] = Number(d.avg_latency);
    });
    return matrix;
  }, [heatmap_data]);

  return (
    <div className="space-y-8">
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="md:col-span-2 rounded-md border border-white/10 bg-slate-900/60 backdrop-blur-md p-4 relative overflow-hidden group">
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-4">
              <Award style={{ color: '#9AED1F' }} size={16} />
              <h3 className="text-[9px] font-bold text-gray-400 uppercase tracking-[0.3em]">Strategic Recommendation</h3>
            </div>
            <div className="flex items-end justify-between">
              <div>
                <p className="text-gray-500 text-[9px] mb-0.5 uppercase font-medium">Top Efficiency Model</p>
                <h2 className="text-xl font-display font-bold text-white tracking-tight">
                  {best_value} <span style={{ color: '#9AED1F' }} className="opacity-80 text-sm">★</span>
                </h2>
                <p className="text-gray-500 text-[9px] mt-2 max-w-sm leading-relaxed uppercase tracking-wider">
                  Optimal balance of economy and speed for clinical workloads.
                </p>
              </div>
              <div className="hidden md:block">
                <div className="px-2 py-1 rounded-md text-[8px] font-bold uppercase tracking-widest border border-[#9AED1F]/20 bg-[#9AED1F]/5 text-[#9AED1F]">
                  Best Value
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-md border border-white/10 bg-slate-900/60 backdrop-blur-md p-4 flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="text-clinical-blue" size={16} />
            <h3 className="text-[9px] font-bold text-gray-500 uppercase tracking-[0.2em]">Usage Volume</h3>
          </div>
          <div>
            <span className="text-2xl font-bold text-white tracking-tighter">
              {daily_trends.reduce((acc, d) => acc + (Number(d.sum_totalTokens) || 0), 0).toLocaleString()}
            </span>
            <span className="text-[9px] font-bold text-gray-500 ml-1.5 uppercase tracking-widest">Tokens</span>
          </div>
          <div className="mt-3 pt-3 border-t border-white/5">
            <div className="flex justify-between items-center text-[9px] font-bold uppercase tracking-widest">
              <span className="text-gray-500">Peak Model</span>
              <span className="text-white truncate max-w-[100px]">{comparison[0]?.model || 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Token & Cost Trend */}
        <div className="rounded-md border border-white/10 bg-slate-900/60 backdrop-blur-md p-6">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Daily Economy Trends</h3>
            <div className="flex gap-6">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#06B6D4' }} />
                <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest">Tokens</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#9AED1F' }} />
                <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest">Cost</span>
              </div>
            </div>
          </div>
          <div className="relative w-full h-[150px]">
            {trendData && (
              <svg viewBox={`0 0 ${trendData.width} ${trendData.height}`} className="w-full h-full overflow-visible">
                {/* Y-Axis Grid */}
                <line x1="0" y1="0" x2={trendData.width} y2="0" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                <line x1="0" y1={trendData.height} x2={trendData.width} y2={trendData.height} stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                <path
                  d={getSmoothPath(trendData.tokenPoints)}
                  fill="none"
                  stroke="#06B6D4"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d={getSmoothPath(trendData.costPoints)}
                  fill="none"
                  stroke="#9AED1F"
                  strokeWidth="3"
                  strokeDasharray="5 7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />

                {/* Token Peak Pinpoint */}
                <circle cx={trendData.tokenPeakCoord.x} cy={trendData.tokenPeakCoord.y} r="5" fill="#06B6D4" />
                <text 
                  x={trendData.tokenPeakCoord.x} 
                  y={trendData.tokenPeakCoord.y - 20} 
                  textAnchor={trendData.tokenPeakCoord.x > 700 ? "end" : "middle"}
                  className="font-display font-black"
                  style={{ fill: '#06B6D4', fontSize: '18px' }}
                >
                  {trendData.maxTokens.toLocaleString()}
                </text>

                {/* Cost Peak Pinpoint */}
                <circle cx={trendData.costPeakCoord.x} cy={trendData.costPeakCoord.y} r="5" fill="#9AED1F" />
                <text 
                  x={trendData.costPeakCoord.x} 
                  y={trendData.costPeakCoord.y - 20} 
                  textAnchor={trendData.costPeakCoord.x > 700 ? "end" : "middle"}
                  className="font-display font-black"
                  style={{ fill: '#9AED1F', fontSize: '18px' }}
                >
                  ${trendData.maxCost.toFixed(4)}
                </text>
              </svg>
            )}
          </div>
          <div className="flex justify-between mt-4 text-[9px] text-gray-600 font-bold uppercase tracking-widest">
            <span>{days_back} Days Ago</span>
            <span>Today</span>
          </div>
        </div>

        {/* Heatmap */}
        <div className="rounded-md border border-white/10 bg-slate-900/60 backdrop-blur-md p-6">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-6">Hourly Latency Stress Heatmap</h3>
          <div className="flex gap-4">
            <div className="flex flex-col justify-between py-1 text-[8px] font-bold text-gray-600 uppercase tracking-tighter w-6">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                <span key={day}>{day}</span>
              ))}
            </div>
            <div className="flex-1">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(24, 1fr)', gap: '4px' }}>
                {heatmapMatrix.flatMap((dayRow, dIdx) =>
                  dayRow.map((lat, hIdx) => {
                    const maxLat = Math.max(...heatmapMatrix.flat(), 1);
                    const intensity = lat ? (0.2 + 0.8 * (lat / maxLat)) : 0;
                    return (
                      <div
                        key={`${dIdx}-${hIdx}`}
                        className="aspect-square rounded-[1px] transition-all cursor-crosshair relative group"
                        style={{
                          backgroundColor: lat ? `rgba(6, 182, 212, ${intensity})` : 'rgba(255, 255, 255, 0.05)',
                          border: 'none'
                        }}
                      >
                        {/* Tooltip */}
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 pointer-events-none">
                          <div className="bg-[#0D1525] border border-white/20 rounded px-2 py-1.5 shadow-2xl whitespace-nowrap">
                            <p className="text-[8px] text-gray-400 font-bold uppercase tracking-widest mb-0.5">
                              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][dIdx]} • {hIdx}:00
                            </p>
                            <p className="text-[10px] text-white font-bold">
                              {lat ? `${lat.toFixed(2)}s Latency` : 'No Activity'}
                            </p>
                          </div>
                          <div className="w-2 h-2 bg-[#0D1525] border-r border-b border-white/20 rotate-45 absolute -bottom-1 left-1/2 -translate-x-1/2" />
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
          <div className="flex justify-between mt-4 text-[8px] text-gray-600 font-bold uppercase tracking-widest px-1">
            <span>12 AM</span><span>12 PM</span><span>11 PM</span>
          </div>
          <div className="mt-6 pt-4 border-t border-white/5">
            <p className="text-[10px] leading-relaxed text-gray-400 font-medium italic">
              Intensity reflects system stress (latency peaks).
            </p>
          </div>
        </div>
      </div>

      {/* Benchmarking Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-md border border-white/10 bg-slate-900/60 backdrop-blur-md p-6">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Usage & Economy</h3>
            <span className="text-[9px] font-bold text-gray-600 uppercase tracking-widest">Total Tokens</span>
          </div>
          <div className="space-y-6">
            {comparison.length === 0 && (
              <div className="py-8 text-center text-gray-600 text-[10px] font-bold uppercase tracking-widest">No model data detected</div>
            )}
            {comparison.slice().sort((a, b) => (Number(b.sum_totalTokens) || 0) - (Number(a.sum_totalTokens) || 0)).slice(0, 5).map((model) => {
              const maxTokens = Math.max(...comparison.map(m => Number(m.sum_totalTokens) || 1));
              const currentTokens = Number(model.sum_totalTokens) || 0;
              return (
                <div key={model.model}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[10px] font-bold text-white uppercase tracking-wider">{model.model}</span>
                    <span style={{ color: '#9AED1F' }} className="text-[10px] font-bold">
                      {currentTokens.toLocaleString()} <span className="text-[8px] opacity-60">Tokens</span>
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="h-full transition-all duration-1000"
                      style={{ backgroundColor: '#9AED1F', width: `${Math.max((currentTokens / maxTokens) * 100, 2)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="rounded-md border border-white/10 bg-slate-900/60 backdrop-blur-md p-6">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">System Responsiveness</h3>
            <span className="text-[9px] font-bold text-gray-600 uppercase tracking-widest">Avg Latency</span>
          </div>
          <div className="space-y-6">
            {comparison.slice().sort((a, b) => (Number(a.raw_latency) || 0) - (Number(b.raw_latency) || 0)).slice(0, 5).map((model) => {
              const maxLatency = Math.max(...comparison.map(m => Number(m.raw_latency) || 1));
              const currentLatency = Number(model.raw_latency) || 0;
              return (
                <div key={model.model}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[10px] font-bold text-white uppercase tracking-wider">{model.model}</span>
                    <span className="text-clinical-blue text-[10px] font-bold">{model.avg_latency}</span>
                  </div>
                  <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-clinical-blue transition-all duration-1000"
                      style={{ width: `${Math.max((currentLatency / maxLatency) * 100, 2)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

    </div>
  );
};

export default OperationalView;
