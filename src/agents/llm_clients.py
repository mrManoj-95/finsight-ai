import os
from functools import lru_cache
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def _resolve_temperature(env_var: str, default: float) -> float:
    raw = os.getenv(env_var)
    if raw is None:
        return default
    return float(raw)


@lru_cache(maxsize=None)
def get_deepseek_llm() -> ChatOpenAI:
    """Planner + Verifier — structured reasoning / guardrail tasks."""
    kwargs = {
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    }
    temp = _resolve_temperature("DEEPSEEK_TEMPERATURE", default=0)
    if temp is not None:
        kwargs["temperature"] = temp
    return ChatOpenAI(**kwargs)


@lru_cache(maxsize=None)
def get_gemini_llm() -> ChatOpenAI:
    """Retriever query-expansion + Table QA reasoning."""
    kwargs = {
        "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "api_key": os.getenv("GEMINI_API_KEY"),
        "base_url": os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"),
    }
    temp = _resolve_temperature("GEMINI_TEMPERATURE", default=0)
    if temp is not None:
        kwargs["temperature"] = temp
    return ChatOpenAI(**kwargs)


@lru_cache(maxsize=None)
def get_kimi_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("MOONSHOT_MODEL", "kimi-k2.6"),
        api_key=os.getenv("MOONSHOT_API_KEY"),
        base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1"),
        temperature=_resolve_temperature("MOONSHOT_TEMPERATURE", default=1),
    )