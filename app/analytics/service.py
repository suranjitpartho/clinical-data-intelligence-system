import os
import datetime
from langfuse import Langfuse
from app.analytics.sync import obs_sync_service
from app.db.base import SessionLocal
from sqlalchemy import func, desc


class AnalyticsService:
    def __init__(self):
        self.langfuse = None
        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            try:
                self.langfuse = Langfuse(
                    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                    host=os.getenv("LANGFUSE_HOST"),
                )
            except Exception:
                pass
        self._cache_duration = datetime.timedelta(minutes=5)

    def get_system_metrics(self, days_back: int = 7, page: int = 1, page_size: int = 10):
        from app.models.observability import InferenceTrace, InferenceSpan

        db = SessionLocal()
        now = datetime.datetime.now(datetime.timezone.utc)
        from_date = now - datetime.timedelta(days=days_back)

        try:
            summary_res = db.query(
                func.count(InferenceTrace.id).label("total"),
                func.sum(InferenceTrace.total_tokens).label("tokens"),
                func.sum(InferenceTrace.total_cost).label("cost"),
            ).filter(InferenceTrace.timestamp >= from_date).first()

            avg_lat = db.query(func.avg(InferenceTrace.total_latency)).filter(
                InferenceTrace.timestamp >= from_date, InferenceTrace.status == "SUCCESS"
            ).scalar() or 0.0

            error_count = db.query(func.count(InferenceTrace.id)).filter(
                InferenceTrace.timestamp >= from_date, InferenceTrace.status == "ERROR"
            ).scalar() or 0

            total_count = db.query(InferenceTrace).filter(InferenceTrace.timestamp >= from_date).count()
            traces = (
                db.query(InferenceTrace)
                .filter(InferenceTrace.timestamp >= from_date)
                .order_by(desc(InferenceTrace.timestamp))
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )

            trace_list = []
            for t in traces:
                trace_list.append({
                    "id": str(t.trace_id),
                    "request_id": t.request_id,
                    "session_id": t.session_id,
                    "timestamp": t.timestamp.isoformat(),
                    "input": t.input_preview or "Clinical Consultation",
                    "output": t.output_preview or "",
                    "total_latency": f"{t.total_latency:.2f}s",
                    "total_tokens": int(t.total_tokens or 0),
                    "total_cost": float(t.total_cost or 0),
                    "status": t.status,
                    "error_message": t.error_message,
                    "sql_query": t.sql_query,
                    "steps": [
                        {
                            "name": s.name,
                            "latency": f"{s.latency:.2f}s",
                            "tokens": s.total_tokens,
                            "cost": float(s.total_cost or 0),
                            "status": s.status or "SUCCESS",
                            "input_data": s.input_data,
                            "output_data": s.output_data,
                        }
                        for s in sorted(t.spans, key=lambda x: x.start_time or datetime.datetime.min)
                    ],
                })

            agg_tokens = float(summary_res.tokens or 0)
            agg_cost = float(summary_res.cost or 0)
            avg_lat = float(avg_lat)
            return {
                "summary": {
                    "total_queries": int(summary_res.total or 0),
                    "error_queries": int(error_count),
                    "avg_latency": f"{avg_lat:.2f}s",
                    "total_tokens": f"{agg_tokens/1000:.1f}k" if agg_tokens > 1000 else str(int(agg_tokens)),
                    "total_cost": f"${agg_cost:.5f}" if agg_cost > 0 else "$0.00000",
                },
                "pagination": {
                    "current_page": page,
                    "total_pages": (total_count // page_size) + (1 if total_count % page_size > 0 else 0),
                    "total_items": total_count,
                    "page_size": page_size,
                },
                "recent_traces": trace_list,
                "cached_at": now.strftime("%H:%M:%S"),
            }
        finally:
            db.close()

    def get_operational_analytics(self, days_back: int = 7, model_filter: str = None):
        from app.models.observability import InferenceTrace, InferenceSpan

        db = SessionLocal()
        now = datetime.datetime.now(datetime.timezone.utc)
        from_date = now - datetime.timedelta(days=days_back)

        try:
            daily_query = (
                db.query(
                    func.date(InferenceTrace.timestamp).label("date"),
                    func.sum(InferenceTrace.total_tokens).label("tokens"),
                    func.sum(InferenceTrace.total_cost).label("cost"),
                )
                .filter(InferenceTrace.timestamp >= from_date)
                .group_by(func.date(InferenceTrace.timestamp))
                .all()
            )

            db_trends = {str(res.date): (int(res.tokens or 0), float(res.cost or 0)) for res in daily_query}
            local_tz = datetime.datetime.now().astimezone().tzinfo
            now_local = now.astimezone(local_tz)
            from_date_local = from_date.astimezone(local_tz)
            start_date = from_date_local.date()
            end_date = now_local.date()

            formatted_trends = []
            current_date = start_date
            while current_date <= end_date:
                day_str = str(current_date)
                tokens, cost = db_trends.get(day_str, (0, 0.0))
                formatted_trends.append({
                    "time_dimension": f"{day_str}T00:00:00Z",
                    "sum_totalTokens": tokens,
                    "sum_totalCost": cost,
                })
                current_date += datetime.timedelta(days=1)

            hour_query = (
                db.query(
                    func.date_trunc("hour", InferenceTrace.timestamp).label("hour"),
                    func.avg(InferenceTrace.total_latency).label("avg_lat"),
                )
                .filter(
                    InferenceTrace.timestamp >= from_date,
                    InferenceTrace.status == "SUCCESS",
                )
                .group_by(func.date_trunc("hour", InferenceTrace.timestamp))
                .all()
            )

            formatted_heatmap = []
            for res in hour_query:
                dt = res.hour
                if dt and dt.tzinfo:
                    dt = dt.astimezone(datetime.timezone.utc)
                formatted_heatmap.append({
                    "time_dimension": dt.strftime("%Y-%m-%dT%H:00:00Z") if dt else None,
                    "avg_latency": float(res.avg_lat or 0),
                })

            model_query = (
                db.query(
                    InferenceSpan.model,
                    func.count(InferenceSpan.id).label("queries"),
                    func.avg(InferenceTrace.total_latency).label("avg_lat"),
                    func.sum(InferenceTrace.total_tokens).label("tokens"),
                    func.sum(InferenceTrace.total_cost).label("cost"),
                )
                .join(InferenceTrace, InferenceTrace.trace_id == InferenceSpan.trace_id)
                .filter(
                    InferenceSpan.name == "SYNTHESIS",
                    InferenceSpan.model != None,
                    InferenceSpan.model != "N/A",
                    InferenceTrace.status == "SUCCESS",
                    InferenceTrace.total_latency > 0,
                    InferenceTrace.timestamp >= from_date,
                )
                .group_by(InferenceSpan.model)
                .all()
            )

            formatted_comparison = []
            best_model = None
            min_score = float("inf")
            available_models = []

            for res in model_query:
                m_name = (res.model or "Unknown").upper()
                available_models.append(m_name)
                avg_lat = float(res.avg_lat or 0)
                cost_per_token = float(res.cost or 0) / int(res.tokens or 1)
                value_score = cost_per_token * (avg_lat + 1)

                formatted_comparison.append({
                    "model": m_name,
                    "queries": int(res.queries),
                    "avg_latency": f"{avg_lat:.2f}s",
                    "raw_latency": avg_lat,
                    "total_cost": float(res.cost or 0),
                    "sum_totalTokens": int(res.tokens or 0),
                    "value_score": value_score,
                })
                if 0 < value_score < min_score:
                    min_score = value_score
                    best_model = m_name

            costs_query = (
                db.query(
                    func.sum(InferenceSpan.input_cost).label("input_cost"),
                    func.sum(InferenceSpan.output_cost).label("output_cost"),
                )
                .join(InferenceTrace, InferenceTrace.trace_id == InferenceSpan.trace_id)
                .filter(InferenceTrace.timestamp >= from_date)
                .first()
            )
            total_input_cost = float(costs_query.input_cost or 0.0) if costs_query else 0.0
            total_output_cost = float(costs_query.output_cost or 0.0) if costs_query else 0.0

            return {
                "daily_trends": formatted_trends,
                "heatmap_data": formatted_heatmap,
                "comparison": sorted(formatted_comparison, key=lambda x: x["queries"], reverse=True),
                "available_models": available_models,
                "best_value": best_model or "N/A",
                "total_input_cost": total_input_cost,
                "total_output_cost": total_output_cost,
                "cached_at": now.strftime("%H:%M:%S"),
            }
        finally:
            db.close()


analytics_service = AnalyticsService()
