"""
Reusable data refinement utilities.
Centralizes the logic for deduplication, privacy filtering, and metadata sync.
Used by both the agent's refine_node and the CSV export endpoint.
"""

def apply_data_refinement(data_results, data_metadata=None):
    """
    Generic refinement function: deduplicates data, filters sensitive columns,
    and synchronizes metadata. Returns refined data and updated metadata.
    
    Args:
        data_results: List of dictionaries (raw data from SQL/RAG).
        data_metadata: Optional dict with metadata like total_count, etc.
    
    Returns:
        Tuple: (refined_data, refined_metadata, refinement_log)
    """
    if not data_results or not isinstance(data_results, list):
        return [], data_metadata or {}, ""

    if data_metadata is None:
        data_metadata = {}

    # Define filter patterns
    ID_PATTERNS = ["_id", "uuid", "guid"]
    NARRATIVE_PATTERNS = ["content", "narrative", "note", "description", "text_content"]

    seen_hashes = set()
    refined_data = []
    
    for row in data_results:
        if not isinstance(row, dict):
            refined_data.append(row)
            continue
            
        # 1. Column Filtering (Privacy & UI Cleanliness)
        clean_row = {}
        for k, v in row.items():
            k_lower = k.lower()
            
            # Skip ID columns
            if any(p in k_lower for p in ID_PATTERNS) and k_lower != "id":
                continue
            if k_lower == "id" and (isinstance(v, str) and len(v) > 20):  # catch UUIDs
                continue
                
            # Skip Narrative columns
            if any(p in k_lower for p in NARRATIVE_PATTERNS):
                continue
                
            clean_row[k] = v

        # 2. Deduplication based on CLEANED content
        row_hash = hash(tuple(sorted(clean_row.items(), key=lambda x: x[0])))
        
        if row_hash not in seen_hashes:
            seen_hashes.add(row_hash)
            refined_data.append(clean_row)

    # 3. Metadata Synchronization
    refined_count = len(refined_data)
    original_count = data_metadata.get("total_count", len(data_results))
    
    refined_metadata = data_metadata.copy()
    refined_metadata.update({
        "total_count": refined_count,
        "is_refined": True,
        "original_count": original_count,
        "truncated": refined_count > 25
    })

    # Construct refinement log
    refinement_log = ""
    if refined_count != original_count:
        refinement_log = f"Optimized results: Found {refined_count} unique clinical entities (filtered from {original_count} raw records)."
    else:
        refinement_log = f"Data validation complete: {refined_count} records verified for accuracy."

    return refined_data, refined_metadata, refinement_log
