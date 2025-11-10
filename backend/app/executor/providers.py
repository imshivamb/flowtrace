import os
from typing import Dict, Any, Tuple, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.executor.tracing import emit_event
from sqlalchemy.ext.asyncio import AsyncSession


async def call_llm(
    db: AsyncSession,
    run_id: str,
    step_id: Optional[str],
    provider: str,
    model: str,
    system: str,
    prompt: str,
    temperature: float = 0.0
) -> Tuple[str, Dict[str, int], str]:
    """
    Call LLM provider with fallback support.

    Returns:
        Tuple of (response_text, token_counts, provider_used)
        token_counts: {"input": int, "output": int, "total": int}
    """
    try:
        response, tokens = await _call_provider(provider, model, system, prompt, temperature)
        return response, tokens, provider
    except Exception as primary_error:
        fallback_provider = "gemini" if provider == "openai" else "openai"
        fallback_model = _get_fallback_model(fallback_provider, model)
        await emit_event(db, run_id, step_id, "log", {
            "msg": f"Primary provider {provider} failed, trying {fallback_provider}",
            "error": str(primary_error)
        })
        try:
            response, tokens = await _call_provider(
                fallback_provider, fallback_model, system, prompt, temperature
            )
            await emit_event(
                db, run_id, step_id, "log",
                {
                    "msg": f"Fallback provider {fallback_provider} succeeded",
                }
            )
            return response, tokens, fallback_provider
        except Exception as fallback_error:
            error_msg = f"Fallback provider {fallback_provider} failed: {str(fallback_error)}"
            raise Exception(error_msg)

async def _call_provider(
    provider: str,
    model: str,
    system: str,
    prompt: str,
    temperature: float
) -> Tuple[str, Dict[str, int]]:
    """Call specific LLM Provider"""
    if provider == "openai":
        return await _call_openai(model, system, prompt, temperature)
    elif provider == "gemini":
        return await _call_gemini(model, system, prompt, temperature)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

async def _call_openai(
    model: str,
    system: str,
    prompt: str,
    temperature: float
) -> Tuple[str, Dict[str, int]]:
    """Call OpenAI API"""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=settings.OPENAI_API_KEY,
    )
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = await llm.ainvoke(messages)
    input_tokens = _estimate_tokens(system + prompt)
    output_tokens = _estimate_tokens(response.content)
    return response.content, {
        "input": input_tokens,
        "output": output_tokens,
        "total": input_tokens + output_tokens
    }

async def _call_gemini(
    model: str,
    system: str,
    prompt: str,
    temperature: float
) -> Tuple[str, Dict[str, int]]:
    """Call Google Gemini API"""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")
    llm = ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=settings.GEMINI_API_KEY
    )
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    response = await llm.ainvoke(full_prompt)
    input_tokens = _estimate_tokens(full_prompt)
    output_tokens = _estimate_tokens(response.content)
    return response.content, {
        "input": input_tokens,
        "output": output_tokens,
        "total": input_tokens + output_tokens
    }

def _get_fallback_model(fallback_provider: str, original_model: str) -> str:
    """Get appropriate fallback model based on original model tier"""
    if fallback_provider == "gemini":
        if "gpt-5" in original_model.lower():
            if "fast" in original_model.lower():
                return "gemini-2.5-flash"
            elif "low" in original_model.lower():
                return "gemini-2.5-flash"
            else:
                return "gemini-2.5-pro"
        elif "gpt-4" in original_model.lower():
            if "mini" in original_model.lower():
                return "gemini-2.5-flash"
            else:
                return "gemini-2.5-pro"
        else:
            return "gemini-2.5-flash"
    elif fallback_provider == "openai":
        if "2.5-pro" in original_model.lower():
            return "gpt-5"
        elif "2.5-flash" in original_model.lower() or "flash" in original_model.lower():
            return "gpt-5-fast"
        elif "pro" in original_model.lower():
            return "gpt-5"
        else:
            return "gpt-5-fast"
    return original_model

def _estimate_tokens(text: str) -> int:
    """
    Simple token estimation: ~4 characters per token
    For production, use tiktoken or similar
    """
    return len(text) // 4