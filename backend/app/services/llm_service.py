"""LLM Service for managing multiple model providers"""

import time
from typing import List, Dict, Any, Optional, AsyncIterator
import openai
import anthropic
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from app.core.config import settings


class LLMService:
    """Service for managing LLM providers and routing requests"""

    def __init__(self):
        """Initialize LLM service with configured providers"""
        self.providers = {}

        # Initialize OpenAI if configured
        if settings.openai_api_key:
            self.providers["openai"] = {
                "client": openai.AsyncOpenAI(api_key=settings.openai_api_key),
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
            }

        # Initialize Anthropic if configured
        if settings.anthropic_api_key:
            self.providers["anthropic"] = {
                "client": anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key),
                "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229"]
            }

        # Initialize Ollama (always available for local development)
        self.providers["ollama"] = {
            "base_url": settings.ollama_host,
            "models": ["llama3.1:8b", "llama3.1:70b", "mistral", "codellama"]
        }

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate chat completion using the specified model

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (e.g., 'gpt-4o', 'claude-3-5-sonnet')
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters

        Returns:
            Chat completion response
        """
        provider = self._get_provider_for_model(model)

        if provider == "openai":
            return await self._openai_completion(
                messages, model, temperature, max_tokens, stream, **kwargs
            )
        elif provider == "anthropic":
            return await self._anthropic_completion(
                messages, model, temperature, max_tokens, stream, **kwargs
            )
        elif provider == "ollama":
            return await self._ollama_completion(
                messages, model, temperature, max_tokens, stream, **kwargs
            )
        else:
            raise ValueError(f"Unsupported model: {model}")

    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat completion tokens

        Args:
            messages: List of message dicts
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Token strings as they are generated
        """
        provider = self._get_provider_for_model(model)

        if provider == "openai":
            async for chunk in self._openai_stream(messages, model, temperature, max_tokens, **kwargs):
                yield chunk
        elif provider == "anthropic":
            async for chunk in self._anthropic_stream(messages, model, temperature, max_tokens, **kwargs):
                yield chunk
        elif provider == "ollama":
            async for chunk in self._ollama_stream(messages, model, temperature, max_tokens, **kwargs):
                yield chunk

    def _get_provider_for_model(self, model: str) -> str:
        """Determine which provider to use for a given model"""
        if model.startswith("gpt-"):
            return "openai"
        elif model.startswith("claude-"):
            return "anthropic"
        elif "llama" in model.lower() or "mistral" in model.lower():
            return "ollama"
        else:
            # Default to openai if available
            if "openai" in self.providers:
                return "openai"
            return "ollama"

    async def _openai_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        stream: bool,
        **kwargs
    ) -> Dict[str, Any]:
        """OpenAI completion implementation"""
        client = self.providers["openai"]["client"]

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        )

        if not stream:
            return {
                "id": response.id,
                "model": response.model,
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        return response

    async def _openai_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> AsyncIterator[str]:
        """OpenAI streaming implementation"""
        client = self.providers["openai"]["client"]

        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _anthropic_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        stream: bool,
        **kwargs
    ) -> Dict[str, Any]:
        """Anthropic completion implementation"""
        client = self.providers["anthropic"]["client"]

        # Extract system message if present
        system_message = None
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                filtered_messages.append(msg)

        response = await client.messages.create(
            model=model,
            messages=filtered_messages,
            system=system_message,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
            stream=stream,
            **kwargs
        )

        if not stream:
            return {
                "id": response.id,
                "model": response.model,
                "content": response.content[0].text,
                "role": "assistant",
                "finish_reason": response.stop_reason,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }

        return response

    async def _anthropic_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> AsyncIterator[str]:
        """Anthropic streaming implementation"""
        client = self.providers["anthropic"]["client"]

        # Extract system message
        system_message = None
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                filtered_messages.append(msg)

        async with client.messages.stream(
            model=model,
            messages=filtered_messages,
            system=system_message,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
            **kwargs
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def _ollama_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        stream: bool,
        **kwargs
    ) -> Dict[str, Any]:
        """Ollama completion implementation"""
        import httpx

        base_url = self.providers["ollama"]["base_url"]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens or -1
                    }
                }
            )

            result = response.json()

            return {
                "id": f"ollama-{int(time.time())}",
                "model": model,
                "content": result["message"]["content"],
                "role": result["message"]["role"],
                "finish_reason": "stop",
                "usage": {
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                }
            }

    async def _ollama_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> AsyncIterator[str]:
        """Ollama streaming implementation"""
        import httpx

        base_url = self.providers["ollama"]["base_url"]

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens or -1
                    }
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        import json
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate estimated cost for a completion

        Args:
            model: Model used
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Pricing as of 2024 (per 1K tokens)
        pricing = {
            "gpt-4o": {"input": 0.0025, "output": 0.01},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        }

        # Ollama and self-hosted models have no API cost
        if model not in pricing:
            return 0.0

        model_pricing = pricing[model]
        cost = (prompt_tokens / 1000 * model_pricing["input"]) + \
               (completion_tokens / 1000 * model_pricing["output"])

        return round(cost, 6)
