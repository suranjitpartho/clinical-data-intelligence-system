import os

# 1. Provide-Agnostic LLM Switcher (Dynamic)
def get_llm(provider=None, model_name=None):
    provider = (provider or os.getenv("AI_PROVIDER", "groq")).lower()
    model_name = model_name or os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
    
    if provider == "groq":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name, 
            temperature=0, 
            openai_api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name, temperature=0, api_key=os.getenv("AI_API_KEY"))
    elif provider == "github":
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token or github_token == "your_github_pat_here":
            raise ValueError("GITHUB_TOKEN is missing or not set in .env")
            
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name, 
            temperature=0, 
            api_key=github_token,
            base_url="https://models.inference.ai.azure.com",
            timeout=45,
            max_retries=2
        )
    
    # Default fallback
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=model_name, temperature=0, api_key=os.getenv("AI_API_KEY"))
