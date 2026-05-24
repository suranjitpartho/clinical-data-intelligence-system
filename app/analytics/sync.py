import ast
import datetime
import os
import json
import re
import time
from sqlalchemy.orm import Session
from app.models.observability import InferenceTrace, InferenceSpan
from app.db.base import SessionLocal
from app.analytics.utils import clean_clinical_data, normalize_model_name
from langfuse import Langfuse


class ObservabilitySyncService:
    def __init__(self):
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
            timeout=30,
        )

    def sync_latest(self, days_back: int = 30):
        db = SessionLocal()
        try:
            fetch_from = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_back)
            remote_traces = []
            for page in range(1, 20):
                for attempt in range(3):
                    try:
                        res = self.langfuse.api.trace.list(
                            from_timestamp=fetch_from, limit=100, page=page
                        )
                        data = res.data if hasattr(res, "data") else []
                        remote_traces.extend(data)
                        if len(data) < 100:
                            page = 999
                        time.sleep(0.5)
                        break
                    except Exception as e:
                        wait = (attempt + 1) * 3
                        print(f"[Sync] List page {page} failed (attempt {attempt+1}/3): {e}. Waiting {wait}s...")
                        time.sleep(wait)
                else:
                    print(f"[Sync] Giving up on list page {page} after 3 attempts.")
                    break
                if page == 999:
                    break

            existing_ids = set(row[0] for row in db.query(InferenceTrace.trace_id).all())
            new_traces = [t for t in remote_traces if t.id not in existing_ids]
            print(f"[Sync] Found {len(remote_traces)} remote traces, {len(existing_ids)} already synced, {len(new_traces)} new.")

            synced = 0
            batch_limit = 100
            for i, t_summary in enumerate(new_traces[:batch_limit]):
                for attempt in range(3):
                    try:
                        t_full = self.langfuse.api.trace.get(t_summary.id)
                        self._upsert_trace_data(db, t_full)
                        db.commit()
                        synced += 1
                        print(f"[Sync] ({synced}/{len(new_traces)}) Synced trace {t_summary.id[:12]}...")
                        time.sleep(1)
                        break
                    except Exception as e:
                        err = str(e)
                        if "429" in err or "502" in err or "timed out" in err.lower():
                            wait = (attempt + 1) * 3
                            print(f"[Sync] Rate limited on {t_summary.id[:12]}. Waiting {wait}s (attempt {attempt+1}/3)...")
                            time.sleep(wait)
                        else:
                            print(f"[Sync] Error on trace {t_summary.id[:12]}: {e}")
                            db.rollback()
                            break

            print(f"[Sync] Complete. Synced {synced}/{len(new_traces)} new traces.")
            return {"status": "success", "synced": synced, "total_new": len(new_traces)}
        except Exception as e:
            print(f"[Sync] Fatal error: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            db.close()

    def _upsert_trace_data(self, db: Session, t_full):
        WHITELIST = ["rewrite", "cache_check", "classify", "sql_tool", "rag_tool", "refine", "synthesis"]

        trace_record = db.query(InferenceTrace).filter(InferenceTrace.trace_id == t_full.id).first()
        if not trace_record:
            trace_record = InferenceTrace(trace_id=t_full.id)
            db.add(trace_record)

        trace_record.session_id = getattr(t_full, "session_id", None)
        trace_record.name = t_full.name
        trace_record.timestamp = t_full.timestamp
        trace_record.total_latency = float(getattr(t_full, "latency", 0) or 0)
        trace_record.total_tokens = 0
        trace_record.total_cost = 0.0
        trace_record.status = "ERROR" if getattr(t_full, "level", "DEFAULT") == "ERROR" else "SUCCESS"
        if trace_record.status == "ERROR":
            trace_record.error_message = getattr(t_full, "status_message", "Trace execution failed.")

        raw_input = getattr(t_full, "input", "")
        raw_output = getattr(t_full, "output", "")
        trace_record.input_preview = clean_clinical_data(raw_input)
        trace_record.output_preview = clean_clinical_data(raw_output)

        observations = t_full.observations if hasattr(t_full, "observations") else []
        span_data = {
            name: {
                "ids": [], "tokens": 0, "in": 0, "out": 0, "cost": 0.0,
                "in_cost": 0.0, "out_cost": 0.0, "latency": 0.0,
                "start_time": None, "status": "SUCCESS", "error": None,
                "input": "", "output": "", "model": "N/A",
            }
            for name in WHITELIST
        }

        for obs in observations:
            name_lower = obs.name.lower()
            if name_lower in WHITELIST:
                sd = span_data[name_lower]
                sd["ids"].append(obs.id)
                sd["latency"] += float(getattr(obs, "latency", 0) or 0)
                obs_start = getattr(obs, "start_time", None)
                if obs_start and (sd["start_time"] is None or obs_start < sd["start_time"]):
                    sd["start_time"] = obs_start
                sd["input"] = str(getattr(obs, "input", "") or sd["input"])
                sd["output"] = str(getattr(obs, "output", "") or sd["output"])
                obs_model = normalize_model_name(getattr(obs, "model", "N/A"))
                if obs_model != "N/A":
                    sd["model"] = obs_model
                if getattr(obs, "level", "DEFAULT") == "ERROR":
                    sd["status"] = "ERROR"
                    sd["error"] = str(getattr(obs, "status_message", "Node Error"))

        for obs in observations:
            usage = getattr(obs, "usage", None)
            tokens, in_t, out_t = 0, 0, 0
            if usage:
                if isinstance(usage, dict):
                    in_t = int(usage.get("prompt", usage.get("input", 0)) or 0)
                    out_t = int(usage.get("completion", usage.get("output", 0)) or 0)
                    tokens = int(usage.get("total", 0) or (in_t + out_t))
                else:
                    in_t = int(getattr(usage, "input", 0) or 0)
                    out_t = int(getattr(usage, "output", 0) or 0)
                    tokens = int(getattr(usage, "total", 0) or (in_t + out_t))

            cost = float(getattr(obs, "calculated_total_cost", 0) or 0)
            in_cost = float(getattr(obs, "calculated_input_cost", 0) or 0)
            out_cost = float(getattr(obs, "calculated_output_cost", 0) or 0)

            trace_record.total_tokens += tokens
            trace_record.total_cost += cost

            parent_id = getattr(obs, "parent_observation_id", None)
            if parent_id:
                for name, sd in span_data.items():
                    if parent_id in sd["ids"]:
                        sd["tokens"] += tokens
                        sd["in"] += in_t
                        sd["out"] += out_t
                        sd["cost"] += cost
                        sd["in_cost"] += in_cost
                        sd["out_cost"] += out_cost
                        if obs.type == "GENERATION":
                            sd["model"] = normalize_model_name(getattr(obs, "model", sd["model"]))

        db.query(InferenceSpan).filter(InferenceSpan.trace_id == t_full.id).delete()

        for name, sd in span_data.items():
            if not sd["ids"]:
                continue
            span_record = InferenceSpan(
                span_id=sd["ids"][0],
                trace_id=t_full.id,
                name=name.upper(),
                span_type="NODE",
                model=sd["model"],
                latency=sd["latency"],
                start_time=sd["start_time"],
                input_tokens=sd["in"],
                output_tokens=sd["out"],
                total_tokens=sd["tokens"],
                input_cost=sd["in_cost"],
                output_cost=sd["out_cost"],
                total_cost=sd["cost"],
                input_data=sd["input"],
                output_data=sd["output"],
                status=sd["status"],
                error_message=sd["error"],
            )
            db.add(span_record)
            if sd["status"] == "ERROR":
                trace_record.status = "ERROR"
                trace_record.error_message = sd["error"]

        sql_tool_output = span_data.get("sql_tool", {}).get("output", "")
        if sql_tool_output:
            tool_query = None
            try:
                cleaned = re.sub(r"'<[A-Za-z_]+>'", "0", sql_tool_output)
                data = ast.literal_eval(cleaned)
                if isinstance(data, dict):
                    tool_query = data.get("tool_query")
            except (ValueError, SyntaxError):
                pass
            if not tool_query:
                match = re.search(
                    r"'tool_query':\s*\"(.+?)\"(?=\s*,\s*'(?:logs|reference_context))",
                    sql_tool_output, re.DOTALL,
                )
                if match:
                    tool_query = match.group(1)
            if tool_query and not str(tool_query).startswith("ERROR"):
                trace_record.sql_query = str(tool_query).strip()


obs_sync_service = ObservabilitySyncService()
