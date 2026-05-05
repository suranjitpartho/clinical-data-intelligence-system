import os
import datetime
import json
from langfuse import Langfuse
from concurrent.futures import ThreadPoolExecutor

class AnalyticsService:
    def __init__(self):
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST")
        )
        self._cache = None
        self._last_updated = None
        self._cache_duration = datetime.timedelta(minutes=5)

    def get_system_metrics(self, days_back: int = 7, page: int = 1, page_size: int = 10):
        """Retrieve system metrics from Langfuse with pagination and time filtering."""
        now = datetime.datetime.now()
        from_date = now - datetime.timedelta(days=days_back)
        
        # We bypass cache for paginated/filtered requests to ensure accuracy
        try:
            # 1. Fetch Traces with filters
            # Langfuse SDK uses 'from_timestamp', 'limit', and 'page'
            traces = self.langfuse.api.trace.list(
                from_timestamp=from_date,
                limit=page_size,
                page=page
            )
            
            trace_list = traces.data if hasattr(traces, 'data') else []
            meta = getattr(traces, 'meta', None)
            total_count = getattr(meta, 'total_items', len(trace_list))
            total_pages = getattr(meta, 'total_pages', 1)

            def fetch_trace_details(t):
                try:
                    observations = self.langfuse.api.observations.get_many(trace_id=t.id, limit=50)
                    obs_list = observations.data if hasattr(observations, 'data') else []
                    
                    steps = []
                    trace_tokens = 0
                    node_data = {}
                    
                    sorted_obs = sorted(obs_list, key=lambda x: x.start_time if hasattr(x, 'start_time') else datetime.datetime.min)

                    for obs in sorted_obs:
                        node_name = str(obs.name)
                        if hasattr(obs, 'metadata') and obs.metadata:
                            node_name = obs.metadata.get('langgraph_node') or obs.metadata.get('node') or node_name
                        
                        step_cost = getattr(obs, 'calculated_total_cost', 0) or 0
                        step_tokens = 0
                        if hasattr(obs, 'usage') and obs.usage:
                            u = obs.usage
                            step_tokens = getattr(u, 'total', 0) or (getattr(u, 'input', 0) + getattr(u, 'output', 0)) or 0
                        
                        if node_name not in node_data:
                            node_data[node_name] = {
                                "tokens": 0, "latency": 0, "cost": 0,
                                "first_seen": obs.start_time if hasattr(obs, 'start_time') else datetime.datetime.min
                            }
                        
                        node_data[node_name]["tokens"] += step_tokens
                        node_data[node_name]["cost"] += float(step_cost)
                        node_data[node_name]["latency"] = max(node_data[node_name]["latency"], getattr(obs, 'latency', 0) or 0)

                    sorted_nodes = sorted(node_data.items(), key=lambda x: x[1]['first_seen'])

                    for name, data in sorted_nodes:
                        if any(x in name for x in ["ChatOpenAI", "ChatGroq", "Generation", "LangGraph"]):
                            continue
                        
                        steps.append({
                            "name": name.replace('_', ' ').title(),
                            "latency": f"{data['latency']:.2f}s",
                            "tokens": int(data['tokens']),
                            "cost": float(data['cost'])
                        })
                        trace_tokens += data['tokens']

                    trace_total_cost = float(getattr(t, 'total_cost', 0) or sum(d['cost'] for d in node_data.values()))

                    display_input = "Clinical consultation"
                    try:
                        inp = t.input
                        if isinstance(inp, str) and inp.startswith('{'):
                            try: inp = json.loads(inp.replace("'", '"'))
                            except: pass
                        if isinstance(inp, dict):
                            display_input = inp.get('QUERY') or inp.get('query') or next(iter(inp.values())) or "Query"
                        else:
                            display_input = str(inp)
                    except:
                        display_input = str(t.input)

                    return {
                        "id": t.id,
                        "timestamp": t.timestamp.isoformat() if hasattr(t.timestamp, 'isoformat') else str(t.timestamp),
                        "input": str(display_input)[:150],
                        "total_latency": f"{t.latency:.2f}s" if hasattr(t, 'latency') and t.latency else "N/A",
                        "total_tokens": int(trace_tokens),
                        "total_cost": float(trace_total_cost),
                        "steps": steps,
                        "raw_latency": t.latency or 0
                    }
                except Exception:
                    return None

            # Execute trace hydration in parallel for the current page
            with ThreadPoolExecutor(max_workers=10) as executor:
                detailed_traces = list(filter(None, executor.map(fetch_trace_details, trace_list)))

            # Summary metrics (aggregated for the entire window using Langfuse metrics API)
            agg_tokens = 0
            agg_cost = 0.0
            avg_lat = 0.0
            window_queries = total_count
            
            try:
                metrics_query = {
                    "view": "traces",
                    "metrics": [
                        {"measure": "count", "aggregation": "count"},
                        {"measure": "latency", "aggregation": "avg"},
                        {"measure": "totalCost", "aggregation": "sum"},
                        {"measure": "totalTokens", "aggregation": "sum"}
                    ],
                    "fromTimestamp": from_date.isoformat() + "Z",
                    "toTimestamp": now.isoformat() + "Z"
                }
                metrics_res = self.langfuse.api.metrics.metrics(query=json.dumps(metrics_query))
                if metrics_res.data and len(metrics_res.data) > 0:
                    metrics_data = metrics_res.data[0]
                    if isinstance(metrics_data, dict):
                        agg_tokens = float(metrics_data.get('sum_totalTokens') or 0)
                        agg_cost = float(metrics_data.get('sum_totalCost') or 0)
                        # Latency comes back in milliseconds from the metrics API
                        lat_ms = float(metrics_data.get('avg_latency') or 0)
                        avg_lat = lat_ms / 1000.0 if lat_ms > 0 else 0
                        window_queries = int(metrics_data.get('count_count') or total_count)
                    else:
                        # Fallback if somehow it's an object instead of dict
                        agg_tokens = float(getattr(metrics_data, 'sum_totalTokens', 0) or 0)
                        agg_cost = float(getattr(metrics_data, 'sum_totalCost', 0) or 0)
                        lat_ms = float(getattr(metrics_data, 'avg_latency', 0) or 0)
                        avg_lat = lat_ms / 1000.0 if lat_ms > 0 else 0
                        window_queries = int(getattr(metrics_data, 'count_count', total_count) or total_count)
            except Exception as e:
                # Fallback to page-level aggregation if metrics API fails
                agg_tokens = sum(dt['total_tokens'] for dt in detailed_traces)
                agg_cost = sum(dt['total_cost'] for dt in detailed_traces)
                agg_latencies = [dt['raw_latency'] for dt in detailed_traces if dt['raw_latency'] > 0]
                avg_lat = sum(agg_latencies)/len(agg_latencies) if agg_latencies else 0

            return {
                "summary": {
                    "total_queries": window_queries,
                    "avg_latency": f"{avg_lat:.2f}s",
                    "total_tokens": f"{agg_tokens/1000:.1f}k" if agg_tokens > 0 else "0",
                    "total_cost": f"${agg_cost:.5f}" if agg_cost > 0 else "$0.00000"
                },
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total_count,
                    "page_size": page_size
                },
                "recent_traces": detailed_traces,
                "cached_at": now.strftime("%H:%M:%S")
            }

        except Exception as e:
            return {"error": str(e)}

analytics_service = AnalyticsService()
