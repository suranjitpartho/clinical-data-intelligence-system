from app.db.base import SessionLocal
from app.agent.state import AgentState
from app.agent.exceptions import GraphNodeError
from app.services.search import get_clinical_notes_semantic


def rag_node(state: AgentState):
    session = SessionLocal()
    search_query = state["query"]

    try:
        if state.get("data_results") and isinstance(state["data_results"], list):
            rows = state["data_results"][:5]
            row_snippets = []
            for row in rows:
                if isinstance(row, dict):
                    row_text = ", ".join(f"{k}: {v}" for k, v in row.items() if v is not None)
                    row_snippets.append(row_text)
            if row_snippets:
                search_query += f". Related records: {'; '.join(row_snippets[:3])[:300]}"

        data = get_clinical_notes_semantic(session, search_query)

        context = [f"Record: {d['content']}" for d in data]
        print(f"[AGENT] RAG SUCCESS: Found {len(data)} results for query: {search_query[:50]}...")
        logs = (
            f"\n• Initiating Semantic Search across clinical notes and institutional guidelines..."
            f"\n• Analyzing narrative patterns related to: '{search_query[:60]}...'"
            f"\n• Successfully retrieved {len(data)} relevant medical records for context synthesis."
        )

        return {"medical_context": context, "logs": logs}
    except Exception as e:
        err = GraphNodeError(str(e), node="rag_tool", code="RAG_ERROR", recoverable=False)
        return {
            "error": {"code": err.code, "message": str(e), "node": err.node, "recoverable": err.recoverable, "details": err.details},
            "medical_context": [],
            "logs": f"\n• Semantic search failed: {e}.",
        }
    finally:
        session.close()
