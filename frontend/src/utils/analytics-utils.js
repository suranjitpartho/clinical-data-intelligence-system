export function parseLatency(s) {
  if (typeof s === 'string') return parseFloat(s.replace('s', ''));
  return s || 0;
}

export function formatLatency(n) {
  return n.toFixed(2) + 's';
}

export function mergeSteps(allSteps) {
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

export function aggregateByRequestId(traces) {
  const reqMap = new Map();
  for (const t of traces) {
    const rid = t.request_id;
    if (!rid) continue;
    if (!reqMap.has(rid)) reqMap.set(rid, []);
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
  return aggregated;
}

export function groupBySession(aggregated) {
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
  return groupedTraces;
}
