from app.services.agent import clinical_agent

def test_agent():
    print("\n--- CLARA: Clinical Assistant Agent Test ---\n")
    
    queries = [
        "How many departments do we have in the clinic?",  # Should trigger SQL
        "Give me a summary of medical notes related to blood tests." # Should trigger RAG/Semantic
    ]
    
    for q in queries:
        print(f"USER QUERY: {q}")
        print("AGENT THINKING...")
        
        initial_state = {
            "query": q,
            "messages": [],
            "next_step": "",
            "data_results": [],
            "final_answer": ""
        }
        
        # Invoke the LangGraph workflow
        result = clinical_agent.invoke(initial_state)
        
        print(f"LOGIC USED: {result['next_step']}")
        print(f"DATA FOUND: {len(result['data_results'])} records")
        print(f"FINAL ANSWER:\n{result['final_answer']}\n")
        print("-" * 50 + "\n")

if __name__ == "__main__":
    test_agent()
