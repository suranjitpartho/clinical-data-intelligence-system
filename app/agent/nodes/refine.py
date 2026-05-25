from app.agent.state import AgentState
from app.agent.exceptions import GraphNodeError
from app.services.refinement_utils import apply_data_refinement


def refine_node(state: AgentState):
    data_results = state.get("data_results", [])
    metadata = state.get("data_metadata", {})

    if not data_results or not isinstance(data_results, list):
        return {}

    try:
        refined_data, refined_metadata, refinement_log = apply_data_refinement(data_results, metadata)
    except Exception as e:
        err = GraphNodeError(str(e), node="refine", code="REFINE_ERROR", recoverable=False)
        return {
            "error": {"code": err.code, "message": str(e), "node": err.node, "recoverable": err.recoverable, "details": err.details},
            "logs": f"\n• Data refinement failed: {e}.",
        }

    medical_context = state.get("medical_context", [])
    filtered_medical_context = []
    context_logs = ""

    if medical_context and refined_data:
        identifiers = set()
        for row in refined_data:
            for k, v in row.items():
                if isinstance(v, str) and len(v) > 2:
                    k_lower = k.lower()
                    if any(id_key in k_lower for id_key in ["name", "patient", "mrn", "nhi", "id"]):
                        identifiers.add(v.strip().lower())

        if identifiers:
            original_context_count = len(medical_context)
            for doc in medical_context:
                if any(ident in doc.lower() for ident in identifiers):
                    filtered_medical_context.append(doc)

            if len(filtered_medical_context) < original_context_count:
                context_logs = f"\n• Medical context refined: {len(filtered_medical_context)} relevant documents retained (from {original_context_count} raw documents)."
            else:
                context_logs = f"\n• Medical context validated: {len(filtered_medical_context)} documents verified."
        else:
            context_logs = "\n• No specific identifiers found in data_results to refine medical context."
            filtered_medical_context = medical_context
    else:
        filtered_medical_context = medical_context

    logs = f"\n• {refinement_log}" + context_logs

    return {
        "data_results": refined_data,
        "data_metadata": refined_metadata,
        "medical_context": filtered_medical_context,
        "logs": logs,
    }
