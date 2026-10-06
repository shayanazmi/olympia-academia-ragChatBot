"""
NVIDIA NIM (Inference Microservice) Client for Olympia Academia
Provides OpenAI-compatible API interaction with exponential backoff retry logic for 429 and 5xx errors.
"""

import os
import time
import json
import random
import logging
from typing import List, Dict, Any, Generator, Optional
from src.utils.config import (
    NVIDIA_BASE_URL,
    NVIDIA_API_KEY,
    NVIDIA_PRIMARY_MODEL,
    NVIDIA_FAST_MODEL,
    NVIDIA_TIMEOUT,
)

logger = logging.getLogger(__name__)

class NIMAuthenticationError(Exception):
    """Raised when NVIDIA API key is missing or invalid."""
    pass

class NIMRateLimitError(Exception):
    """Raised when NVIDIA API rate limit (429) is hit and retries are exhausted."""
    pass

class NIMClient:
    """
    Client for NVIDIA NIM microservices.
    Supports both OpenAI SDK and requests-based fallback with built-in retries.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        primary_model: Optional[str] = None,
        fast_model: Optional[str] = None,
        timeout: int = NVIDIA_TIMEOUT,
    ):
        self.api_key = api_key or NVIDIA_API_KEY or os.getenv("NVIDIA_API_KEY", "")
        self.base_url = (base_url or NVIDIA_BASE_URL or "https://integrate.api.nvidia.com/v1").rstrip("/")
        self.primary_model = primary_model or NVIDIA_PRIMARY_MODEL
        self.fast_model = fast_model or NVIDIA_FAST_MODEL
        self.timeout = timeout

        # Initialize OpenAI client if available
        self._openai_client = None
        try:
            from openai import OpenAI
            if self.api_key:
                self._openai_client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    timeout=float(self.timeout),
                )
        except ImportError:
            self._openai_client = None

    def _validate_auth(self):
        if not self.api_key or self.api_key.strip() in ["", "your_api_key_here", "nvapi-..."]:
            raise NIMAuthenticationError(
                "NVIDIA_API_KEY is not set or invalid. Please add your key to the .env file:\n"
                "NVIDIA_API_KEY=nvapi-your-key-here"
            )

    def _get_headers(self) -> Dict[str, str]:
        self._validate_auth()
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def chat(
        self,
        prompt_or_messages: Any,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.6,
        max_tokens: int = 2048,
        json_mode: bool = False,
        max_retries: int = 3,
    ) -> str:
        """
        Execute a non-streaming chat completion with exponential backoff on 429/5xx.
        Accepts either a string prompt or a list of message dicts.
        """
        self._validate_auth()
        target_model = model or self.primary_model

        if isinstance(prompt_or_messages, str):
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt_or_messages})
        else:
            messages = list(prompt_or_messages)
            if system_prompt and not any(m.get("role") == "system" for m in messages):
                messages.insert(0, {"role": "system", "content": system_prompt})


        for attempt in range(max_retries):
            try:
                # Prefer openai SDK if installed
                if self._openai_client is not None:
                    kwargs: Dict[str, Any] = {
                        "model": target_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                    if json_mode:
                        kwargs["response_format"] = {"type": "json_object"}

                    response = self._openai_client.chat.completions.create(**kwargs)
                    return response.choices[0].message.content or ""

                # Fallback to requests
                import requests
                payload: Dict[str, Any] = {
                    "model": target_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False,
                }
                if json_mode:
                    payload["response_format"] = {"type": "json_object"}

                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=self.timeout,
                )

                if resp.status_code == 401:
                    raise NIMAuthenticationError(f"Authentication failed (401): {resp.text}")
                elif resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 2 ** (attempt + 1)))
                    jitter = random.uniform(0.5, 1.5)
                    sleep_time = min(retry_after + jitter, 15)
                    logger.warning(f"NIM Rate limit (429). Retrying in {sleep_time:.1f}s (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(sleep_time)
                    continue
                elif resp.status_code in [500, 502, 503, 504]:
                    sleep_time = 2 * (attempt + 1)
                    logger.warning(f"NIM Server error ({resp.status_code}). Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                    continue

                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]

            except NIMAuthenticationError:
                raise
            except Exception as e:
                err_str = str(e)
                if "401" in err_str or "unauthorized" in err_str.lower():
                    raise NIMAuthenticationError(f"NVIDIA API Key rejected: {err_str}")
                if "429" in err_str or "rate limit" in err_str.lower():
                    sleep_time = (2 ** (attempt + 1)) + random.uniform(0.5, 1.0)
                    logger.warning(f"Rate limit hit. Retrying in {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                    continue
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2)

        raise NIMRateLimitError("Exhausted retries due to rate limits or API downtime.")

    def chat_stream(
        self,
        prompt_or_messages: Any,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.6,
        max_tokens: int = 2048,
    ) -> Generator[str, None, None]:
        """
        Execute streaming chat completion yielding content tokens.
        Accepts either a string prompt or a list of message dicts.
        """
        self._validate_auth()
        target_model = model or self.primary_model

        if isinstance(prompt_or_messages, str):
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt_or_messages})
        else:
            messages = list(prompt_or_messages)
            if system_prompt and not any(m.get("role") == "system" for m in messages):
                messages.insert(0, {"role": "system", "content": system_prompt})

        if self._openai_client is not None:
            try:
                stream = self._openai_client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception as e:
                logger.error(f"OpenAI SDK streaming error: {e}")
                # Fall through to requests if SDK fails

        import requests
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self._get_headers(),
            json=payload,
            timeout=self.timeout,
            stream=True,
        )

        if resp.status_code == 401:
            raise NIMAuthenticationError(f"Invalid API Key (401): {resp.text}")
        elif resp.status_code == 429:
            raise NIMRateLimitError("NVIDIA NIM Rate Limit hit. Please wait a moment.")
        resp.raise_for_status()

        for line in resp.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: "):
                data_str = line_str[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except Exception:
                    continue

_client_instance = None

def get_nim_client() -> NIMClient:
    """Singleton access to NIMClient instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = NIMClient()
    return _client_instance

