"""
MACH-1 API Router
Routes LLM requests through fallback chains with rate limiting.
Groq → Mistral → Ollama → Google (last resort)
"""
import time
import json
import requests
from datetime import datetime, date
from typing import Optional
from collections import defaultdict

from config import settings
from utils.logger import get_logger
from utils.database import db

log = get_logger("mach1.router")


class RateLimiter:
    """Simple daily/per-second rate limiter."""

    def __init__(self):
        self._daily_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._last_call: dict[str, float] = {}

    def _today(self) -> str:
        return date.today().isoformat()

    def can_call(self, provider: str) -> bool:
        today = self._today()
        count = self._daily_counts[today][provider]

        if provider == "groq" and count >= settings.GROQ_RPD:
            return False
        if provider == "google" and count >= settings.GOOGLE_RPD:
            return False
        if provider == "mistral":
            last = self._last_call.get("mistral", 0)
            if time.time() - last < (1.0 / settings.MISTRAL_RPS):
                return False
        return True

    def record_call(self, provider: str):
        today = self._today()
        self._daily_counts[today][provider] += 1
        self._last_call[provider] = time.time()

    def get_usage(self) -> dict:
        today = self._today()
        return dict(self._daily_counts.get(today, {}))


rate_limiter = RateLimiter()


def _call_groq(model: str, messages: list, temperature: float = 0.7,
               max_tokens: int = 2048) -> dict:
    """Call Groq API."""
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "content": data["choices"][0]["message"]["content"],
        "tokens_in": data.get("usage", {}).get("prompt_tokens", 0),
        "tokens_out": data.get("usage", {}).get("completion_tokens", 0),
    }


def _call_mistral(model: str, messages: list, temperature: float = 0.7,
                  max_tokens: int = 2048) -> dict:
    """Call Mistral API."""
    resp = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "content": data["choices"][0]["message"]["content"],
        "tokens_in": data.get("usage", {}).get("prompt_tokens", 0),
        "tokens_out": data.get("usage", {}).get("completion_tokens", 0),
    }


def _call_ollama(model: str, messages: list, temperature: float = 0.7,
                 max_tokens: int = 2048) -> dict:
    """Call local Ollama."""
    resp = requests.post(
        f"{settings.OLLAMA_HOST}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "stream": False,
        },
        timeout=300,  # Local models can be slow
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "content": data.get("message", {}).get("content", ""),
        "tokens_in": data.get("prompt_eval_count", 0),
        "tokens_out": data.get("eval_count", 0),
    }


def _call_google(model: str, messages: list, temperature: float = 0.7,
                 max_tokens: int = 2048) -> dict:
    """Call Google AI Studio (Gemini). LAST RESORT ONLY."""
    # Convert OpenAI-style messages to Gemini format
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        if msg["role"] == "system":
            # Gemini handles system as first user message
            contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        else:
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GOOGLE_AI_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    usage = data.get("usageMetadata", {})
    return {
        "content": text,
        "tokens_in": usage.get("promptTokenCount", 0),
        "tokens_out": usage.get("candidatesTokenCount", 0),
    }


# Provider dispatch
_PROVIDERS = {
    "groq": _call_groq,
    "mistral": _call_mistral,
    "ollama": _call_ollama,
    "google": _call_google,
}


def call_llm(
    team: str,
    messages: list,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    force_provider: str = None,
) -> Optional[dict]:
    """
    Route an LLM call through the team's fallback chain.

    Returns dict with: content, provider, model, tokens_in, tokens_out, latency_ms
    Or None if ALL providers failed.
    """
    # Build the chain
    if force_provider:
        # Force a specific provider (for testing)
        team_config = settings.TEAM_MODELS.get(team, settings.TEAM_MODELS["ceo"])
        model = None
        for p, m in team_config["chain"]:
            if p == force_provider:
                model = m
                break
        if not model:
            log.error(f"Provider {force_provider} not in {team}'s chain")
            return None
        chain = [(force_provider, model)]
    else:
        team_config = settings.TEAM_MODELS.get(team, settings.TEAM_MODELS["ceo"])
        chain = list(team_config["chain"])
        # Google always last
        chain.append(settings.GOOGLE_FALLBACK)

    for provider, model in chain:
        # Check rate limits
        if not rate_limiter.can_call(provider):
            log.debug(f"Rate limited: {provider}, skipping")
            continue

        # Check API key exists (except ollama)
        if provider == "groq" and not settings.GROQ_API_KEY:
            continue
        if provider == "mistral" and not settings.MISTRAL_API_KEY:
            continue
        if provider == "google" and not settings.GOOGLE_AI_KEY:
            continue

        try:
            log.debug(f"Calling {provider}/{model} for team={team}")
            start = time.time()

            call_fn = _PROVIDERS[provider]
            result = call_fn(model, messages, temperature, max_tokens)

            latency = int((time.time() - start) * 1000)
            rate_limiter.record_call(provider)

            # Log to database
            db.log_api_call(
                provider=provider,
                model=model,
                team=team,
                tokens_in=result["tokens_in"],
                tokens_out=result["tokens_out"],
                latency_ms=latency,
                success=True,
            )

            log.info(
                f"✓ {provider}/{model} → {result['tokens_out']} tok in {latency}ms"
            )

            return {
                "content": result["content"],
                "provider": provider,
                "model": model,
                "tokens_in": result["tokens_in"],
                "tokens_out": result["tokens_out"],
                "latency_ms": latency,
            }

        except Exception as e:
            log.warning(f"✗ {provider}/{model} failed: {e}")
            db.log_api_call(
                provider=provider,
                model=model,
                team=team,
                success=False,
                error=str(e)[:500],
            )
            continue

    log.error(f"ALL providers failed for team={team}")
    return None


def call_llm_json(team: str, messages: list, **kwargs) -> Optional[dict]:
    """Call LLM and parse JSON from response. Returns parsed dict or None."""
    result = call_llm(team, messages, **kwargs)
    if not result:
        return None

    content = result["content"]

    # Try to extract JSON from markdown code blocks
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    # Fix common LLM quirks that break JSON
    import re
    # Remove markdown links: [text](url) → text
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    # Remove trailing commas before } or ]
    content = re.sub(r',\s*([}\]])', r'\1', content)

    try:
        parsed = json.loads(content.strip())
        result["parsed"] = parsed
        return result
    except json.JSONDecodeError as e:
        log.warning(f"Failed to parse JSON from {result['provider']}: {e}")
        log.debug(f"Raw content (first 500 chars): {content[:500]}")
        result["parsed"] = None
        return result
