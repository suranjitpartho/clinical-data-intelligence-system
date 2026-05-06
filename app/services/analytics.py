import os
import datetime
import json
from langfuse import Langfuse
from app.db.base import SessionLocal
from sqlalchemy import func, desc

class AnalyticsService:
    def __init__(self):
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST")
        )
        self._cache_duration = datetime.timedelta(minutes=5)

    def get_system_metrics(self, days_back: int = 7, page: int = 1, page_size: int = 10):
        """Retrieve system metrics from the Local Observability Cache.
        Provides instant, paginated access to all traces and their deep details.
        """
        from app.models.observability import InferenceTrace, InferenceSpan
        from app.db.base import SessionLocal
        from sqlalchemy import desc
        
        db = SessionLocal()
        now = datetime.datetime.now(datetime.timezone.utc)
        from_date = now - datetime.timedelta(days=days_back)
        
        try:
            # 2. Get Overall Summary — counts/tokens/cost include all traces; avg latency only from SUCCESS
            summary_res = db.query(
                func.count(InferenceTrace.id).label('total'),
                func.sum(InferenceTrace.total_tokens).label('tokens'),
                func.sum(InferenceTrace.total_cost).label('cost')
            ).filter(InferenceTrace.timestamp >= from_date).first()

            # Avg latency: SUCCESS traces only (excludes token-limit crashes / errors)
            avg_lat = db.query(func.avg(InferenceTrace.total_latency)).filter(
                InferenceTrace.timestamp >= from_date,
                InferenceTrace.status == 'SUCCESS'
            ).scalar() or 0.0

            # 3. Get Recent Traces (Paginated)
            total_count = db.query(InferenceTrace).filter(InferenceTrace.timestamp >= from_date).count()
            
            traces = db.query(InferenceTrace).filter(
                InferenceTrace.timestamp >= from_date
            ).order_by(desc(InferenceTrace.timestamp)).offset((page - 1) * page_size).limit(page_size).all()

            trace_list = []
            for t in traces:
                trace_list.append({
                    "id": str(t.trace_id),
                    "session_id": t.session_id,
                    "timestamp": t.timestamp.isoformat(),
                    "input": t.input_preview or "Clinical Consultation",
                    "output": t.output_preview or "",
                    "total_latency": f"{t.total_latency:.2f}s",
                    "total_tokens": int(t.total_tokens or 0),
                    "total_cost": float(t.total_cost or 0),
                    "status": t.status,
                    "error_message": t.error_message,
                    "steps": [
                        {
                            "name": s.name,
                            "latency": f"{s.latency:.2f}s",
                            "tokens": s.total_tokens,
                            "cost": float(s.total_cost or 0),
                            "status": s.status or "SUCCESS",
                            "input_data": s.input_data,
                            "output_data": s.output_data
                        } for s in sorted(t.spans, key=lambda x: x.start_time or datetime.datetime.min)
                    ]
                })

            agg_tokens = float(summary_res.tokens or 0)
            agg_cost = float(summary_res.cost or 0)
            avg_lat = float(avg_lat)

            return {
                "summary": {
                    "total_queries": int(summary_res.total or 0),
                    "avg_latency": f"{avg_lat:.2f}s",
                    "total_tokens": f"{agg_tokens/1000:.1f}k" if agg_tokens > 1000 else str(int(agg_tokens)),
                    "total_cost": f"${agg_cost:.5f}" if agg_cost > 0 else "$0.00000"
                },
                "pagination": {
                    "current_page": page,
                    "total_pages": (total_count // page_size) + (1 if total_count % page_size > 0 else 0),
                    "total_items": total_count,
                    "page_size": page_size
                },
                "recent_traces": trace_list,
                "cached_at": now.strftime("%H:%M:%S")
            }
        finally:
            db.close()

    def get_operational_analytics(self, days_back: int = 7, model_filter: str = None):
        """High-Performance Aggregator using the Local Observability Cache."""
        from app.services.observability_sync import obs_sync_service
        from app.models.observability import InferenceTrace, InferenceSpan
        
        db = SessionLocal()
        now = datetime.datetime.now(datetime.timezone.utc)
        from_date = now - datetime.timedelta(days=days_back)
        
        try:
            # 1. Daily Trends
            daily_query = db.query(
                func.date(InferenceTrace.timestamp).label('date'),
                func.sum(InferenceTrace.total_tokens).label('tokens'),
                func.sum(InferenceTrace.total_cost).label('cost')
            ).filter(InferenceTrace.timestamp >= from_date).group_by(func.date(InferenceTrace.timestamp)).all()
            
            formatted_trends = [
                {
                    "time_dimension": f"{res.date}T00:00:00Z",
                    "sum_totalTokens": int(res.tokens or 0),
                    "sum_totalCost": float(res.cost or 0)
                } for res in sorted(daily_query, key=lambda x: x.date)
            ]

            # 2. Hourly Heatmap
            hour_query = db.query(
                func.date_trunc('hour', InferenceTrace.timestamp).label('hour'),
                func.avg(InferenceTrace.total_latency).label('avg_lat')
            ).filter(InferenceTrace.timestamp >= from_date).group_by(func.date_trunc('hour', InferenceTrace.timestamp)).all()

            formatted_heatmap = [
                {
                    "time_dimension": res.hour.strftime("%Y-%m-%dT%H:00:00Z"),
                    "avg_latency": float(res.avg_lat or 0)
                } for res in hour_query
            ]

            # 3. Model Benchmarking
            # avg_latency only uses spans where latency > 0 (excludes unexecuted placeholder nodes)
            # Excludes model=None and model='N/A' (nodes without an LLM generation)
            model_query = db.query(
                InferenceSpan.model,
                func.count(InferenceSpan.id).label('queries'),
                func.avg(InferenceSpan.latency).filter(InferenceSpan.latency > 0).label('avg_lat'),
                func.sum(InferenceSpan.total_tokens).label('tokens'),
                func.sum(InferenceSpan.total_cost).label('cost')
            ).filter(
                InferenceSpan.model != None,
                InferenceSpan.model != 'N/A',
                InferenceSpan.status == 'SUCCESS',
                InferenceSpan.start_time >= from_date
            ).group_by(InferenceSpan.model).all()

            formatted_comparison = []
            best_model = None
            min_score = float('inf')
            available_models = []

            for res in model_query:
                m_name = (res.model or "Unknown").upper()
                available_models.append(m_name)

                avg_lat = float(res.avg_lat or 0)
                cost_per_token = (float(res.cost or 0) / int(res.tokens or 1))
                value_score = cost_per_token * (avg_lat + 1)

                formatted_comparison.append({
                    "model": m_name,
                    "queries": int(res.queries),
                    "avg_latency": f"{avg_lat:.2f}s",
                    "raw_latency": avg_lat,
                    "total_cost": float(res.cost or 0),
                    "sum_totalTokens": int(res.tokens or 0),
                    "value_score": value_score
                })
                
                if 0 < value_score < min_score:
                    min_score = value_score
                    best_model = m_name

            return {
                "daily_trends": formatted_trends,
                "heatmap_data": formatted_heatmap,
                "comparison": sorted(formatted_comparison, key=lambda x: x['queries'], reverse=True),
                "available_models": available_models,
                "best_value": best_model or "N/A",
                "cached_at": now.strftime("%H:%M:%S")
            }
        finally:
            db.close()

analytics_service = AnalyticsService()
