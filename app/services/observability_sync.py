import datetime
import os
import json
import time
from sqlalchemy.orm import Session
from sqlalchemy import func
from langfuse import Langfuse
from app.models.observability import InferenceTrace, InferenceSpan
from app.db.base import SessionLocal

class ObservabilitySyncService:
    def __init__(self):
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
            timeout=30  # Generous timeout for cloud free tier
        )

    def sync_latest(self, days_back: int = 30):
        """
        True Delta Sync: Fetches ALL trace IDs (cheap), then only 
        deep-fetches the ones we don't already have in our DB.
        Runs in the background with proper rate-limit handling.
        """
        db = SessionLocal()
        try:
            fetch_from = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_back)
            
            # 1. Collect ALL trace IDs from Langfuse (list calls are lightweight)
            remote_traces = []
            for page in range(1, 20):
                # Retry each list page up to 3 times
                for attempt in range(3):
                    try:
                        res = self.langfuse.api.trace.list(
                            from_timestamp=fetch_from,
                            limit=100,
                            page=page
                        )
                        data = res.data if hasattr(res, 'data') else []
                        remote_traces.extend(data)
                        if len(data) < 100:
                            page = 999  # break outer loop
                        time.sleep(0.5)
                        break  # success, move to next page
                    except Exception as e:
                        wait = (attempt + 1) * 3
                        print(f"[Sync] List page {page} failed (attempt {attempt+1}/3): {e}. Waiting {wait}s...")
                        time.sleep(wait)
                else:
                    print(f"[Sync] Giving up on list page {page} after 3 attempts.")
                    break
                if page == 999:
                    break
            
            # 2. Find which trace IDs we ALREADY have locally
            existing_ids = set(
                row[0] for row in db.query(InferenceTrace.trace_id).all()
            )
            
            # 3. Filter to only NEW traces we haven't synced yet
            new_traces = [t for t in remote_traces if t.id not in existing_ids]
            
            print(f"[Sync] Found {len(remote_traces)} remote traces, {len(existing_ids)} already synced, {len(new_traces)} new to fetch.")
            
            # 4. Deep-fetch only the new ones, with proper pacing
            synced = 0
            batch_limit = 100 # Increased for 30-day catchup
            for i, t_summary in enumerate(new_traces[:batch_limit]):
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        t_full = self.langfuse.api.trace.get(t_summary.id)
                        self._upsert_trace_data(db, t_full)
                        db.commit()
                        synced += 1
                        print(f"[Sync] ({synced}/{len(new_traces)}) Synced trace {t_summary.id[:12]}...")
                        time.sleep(1)  # 1 req/sec = safe for free tier
                        break
                    except Exception as e:
                        err = str(e)
                        if "429" in err or "502" in err or "timed out" in err.lower():
                            wait = (attempt + 1) * 3  # 3s, 6s, 9s
                            print(f"[Sync] Rate limited on {t_summary.id[:12]}. Waiting {wait}s (attempt {attempt+1}/{max_retries})...")
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

    def _clean_clinical_data(self, data):
        """Extracts human-readable text from complex JSON/LangGraph structures."""
        if not data: return ""
        try:
            # Parse if stringified JSON
            val = json.loads(data) if isinstance(data, str) and (data.startswith('{') or data.startswith('[')) else data
            
            if isinstance(val, dict):
                # Priority keys for clinical queries and answers
                for key in ['final_answer', 'query', 'question', 'answer', 'output', 'input', 'text']:
                    if key in val and val[key]:
                        return str(val[key])
                # Fallback to stringifying the first few keys
                return str(val)[:500]
            elif isinstance(val, list) and len(val) > 0:
                # Handle message lists - get the last content
                last = val[-1]
                if isinstance(last, dict):
                    return last.get('content', str(last))
                return str(last)
            return str(val)
        except:
            return str(data)[:500]

    def _upsert_trace_data(self, db: Session, t_full):
        """Maps Langfuse Trace + Observations to our local Inference & Spans with Parent Rollup."""
        
        # 1. Upsert the Trace (Parent)
        trace_record = db.query(InferenceTrace).filter(InferenceTrace.trace_id == t_full.id).first()
        if not trace_record:
            trace_record = InferenceTrace(trace_id=t_full.id)
            db.add(trace_record)

        trace_record.session_id = getattr(t_full, 'session_id', None)
        trace_record.name = t_full.name
        trace_record.timestamp = t_full.timestamp
        trace_record.total_latency = float(getattr(t_full, 'latency', 0) or 0)
        
        # Recalculate Trace Totals from all children for 100% accuracy
        trace_record.total_tokens = 0
        trace_record.total_cost = 0.0
        
        trace_record.status = "SUCCESS"
        
        # Intelligent Clinical Cleanup for Previews
        raw_input = getattr(t_full, 'input', '')
        raw_output = getattr(t_full, 'output', '')
        trace_record.input_preview = self._clean_clinical_data(raw_input)
        trace_record.output_preview = self._clean_clinical_data(raw_output)
        
        # 2. First Pass: Prepare the 5 Core Clinical Spans
        WHITELIST = ['rewrite', 'classify', 'sql_tool', 'rag_tool', 'synthesis']
        observations = t_full.observations if hasattr(t_full, 'observations') else []
        
        # Local map for rolling up data
        span_data = {name: {"tokens": 0, "in": 0, "out": 0, "cost": 0.0, "latency": 0.0, "start_time": None, "status": "SUCCESS", "error": None, "input": "", "output": "", "id": None, "model": "N/A"} for name in WHITELIST}

        for obs in observations:
            name_lower = obs.name.lower()
            if name_lower in WHITELIST:
                sd = span_data[name_lower]
                sd["id"] = obs.id
                sd["latency"] = float(getattr(obs, 'latency', 0) or 0)
                sd["start_time"] = getattr(obs, 'start_time', None)
                sd["input"] = str(getattr(obs, 'input', ''))
                sd["output"] = str(getattr(obs, 'output', ''))
                sd["model"] = getattr(obs, 'model', 'N/A')
                if getattr(obs, 'level', 'DEFAULT') == 'ERROR':
                    sd["status"] = "ERROR"
                    sd["error"] = str(getattr(obs, 'status_message', 'Node Error'))

        # 3. Second Pass: Roll up all Generations (LLM calls) to Whitelisted Parents
        for obs in observations:
            # Extract usage regardless of observation type
            usage = getattr(obs, 'usage', None)
            tokens, in_t, out_t = 0, 0, 0
            if usage:
                if isinstance(usage, dict):
                    in_t = int(usage.get('prompt', usage.get('input', 0)) or 0)
                    out_t = int(usage.get('completion', usage.get('output', 0)) or 0)
                    tokens = int(usage.get('total', 0) or (in_t + out_t))
                else:
                    in_t = int(getattr(usage, 'input', 0) or 0)
                    out_t = int(getattr(usage, 'output', 0) or 0)
                    tokens = int(getattr(usage, 'total', 0) or (in_t + out_t))
            
            cost = float(getattr(obs, 'calculated_total_cost', 0) or 0)
            
            # Always add to Trace-level totals
            trace_record.total_tokens += tokens
            trace_record.total_cost += cost

            # Rollup to the specific clinical parent node
            parent_id = getattr(obs, 'parent_observation_id', None)
            if parent_id:
                for name, sd in span_data.items():
                    if sd["id"] == parent_id:
                        sd["tokens"] += tokens
                        sd["in"] += in_t
                        sd["out"] += out_t
                        sd["cost"] += cost
                        if obs.type == 'GENERATION':
                            sd["model"] = getattr(obs, 'model', sd["model"])

        # 4. Final Pass: Clear existing noise and Commit Clean Spans
        db.query(InferenceSpan).filter(InferenceSpan.trace_id == t_full.id).delete()
        
        for name, sd in span_data.items():
            if not sd["id"]: continue # Node didn't run

            span_record = InferenceSpan(
                span_id=sd["id"], 
                trace_id=t_full.id,
                name=name.upper(),
                span_type="NODE",
                model=sd["model"],
                latency=sd["latency"],
                start_time=sd["start_time"],
                input_tokens=sd["in"],
                output_tokens=sd["out"],
                total_tokens=sd["tokens"],
                total_cost=sd["cost"],
                input_data=sd["input"],
                output_data=sd["output"],
                status=sd["status"],
                error_message=sd["error"]
            )
            db.add(span_record)

            if sd["status"] == "ERROR":
                trace_record.status = "ERROR"
                trace_record.error_message = sd["error"]

obs_sync_service = ObservabilitySyncService()
