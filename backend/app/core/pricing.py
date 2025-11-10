PRICING_CENTS_PER_1K = {
    ("openai", "gpt-5"): {"input": 300, "output": 1200},
    ("openai", "gpt-5-fast"): {"input": 150, "output": 600},
    ("openai", "gpt-5-low"): {"input": 50, "output": 200},
    ("openai", "gpt-4o-mini"): {"input": 15, "output": 60},
    ("openai", "gpt-4o"): {"input": 250, "output": 1000},
    ("gemini", "gemini-2.5-flash"): {"input": 5, "output": 15},
    ("gemini", "gemini-2.5-pro"): {"input": 12, "output": 35},
    ("gemini", "gemini-pro"): {"input": 5, "output": 15},
    ("gemini", "gemini-1.5-pro"): {"input": 10, "output": 30},
}

def estimate_cost_cents(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> int:
    p = PRICING_CENTS_PER_1K.get((provider, model))
    if not p:
        return 0
    return int((prompt_tokens * p["input"] + completion_tokens * p["output"]) / 1000)
