"""Chat API endpoints with streaming support"""

import json
import time
import uuid
from typing import AsyncIterator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.schemas.conversation import ChatRequest, ChatResponse, ChatChoice, ChatUsage, ChatMessage
from app.services.llm_service import LLMService
from app.services.cache_service import CacheService
from app.services.rag_service import RAGService
from app.services.search_service import SearchService
from app.utils.dependencies import get_current_user
from app.core.config import settings


router = APIRouter(prefix="/chat", tags=["Chat"])

# Initialize services
llm_service = LLMService()
cache_service = CacheService()
rag_service = RAGService()
search_service = SearchService()


@router.post("/completions")
async def chat_completion(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create chat completion (OpenAI compatible endpoint)

    Supports:
    - Multiple LLM providers (OpenAI, Anthropic, Ollama)
    - Streaming responses
    - RAG (document retrieval)
    - Web search
    - Semantic caching
    """

    # Convert messages to dict format
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    # Check cache first (non-streaming only)
    if not request.stream and settings.semantic_cache_enabled:
        cached_response = await cache_service.get_cached_response(messages, request.model)
        if cached_response:
            # Return cached response
            return ChatResponse(
                id=f"cached-{uuid.uuid4()}",
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=cached_response["content"]
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=ChatUsage(
                    prompt_tokens=cached_response["usage"]["prompt_tokens"],
                    completion_tokens=cached_response["usage"]["completion_tokens"],
                    total_tokens=cached_response["usage"]["total_tokens"],
                    estimated_cost=0.0  # Cached responses are free
                )
            )

    # Enhance with RAG if enabled
    if request.rag_enabled and settings.enable_rag:
        # Get last user message
        last_user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                last_user_message = msg.content
                break

        if last_user_message:
            # Search documents
            search_results = await rag_service.search(
                query=last_user_message,
                organization_id=str(current_user.organization_id),
                limit=5
            )

            if search_results:
                # Inject context
                context = "Relevant documents:\n\n"
                for i, result in enumerate(search_results, 1):
                    context += f"{i}. {result['filename']}\n{result['text']}\n\n"

                # Add as system message or prepend to user message
                messages.insert(-1, {
                    "role": "system",
                    "content": f"{context}\nUse the above context to answer the user's question. Cite sources when applicable."
                })

    # Enhance with web search if enabled
    if request.web_search and settings.enable_web_search:
        last_user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                last_user_message = msg.content
                break

        if last_user_message:
            # Perform web search
            search_results = await search_service.search_and_format(
                query=last_user_message,
                max_results=5
            )

            # Inject search results
            messages.insert(-1, {
                "role": "system",
                "content": f"{search_results}\nUse the web search results above to provide an up-to-date answer."
            })

    # Handle streaming
    if request.stream:
        return StreamingResponse(
            stream_chat_response(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                user=current_user,
                conversation_id=request.conversation_id,
                db=db
            ),
            media_type="text/event-stream"
        )

    # Non-streaming response
    try:
        completion = await llm_service.chat_completion(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False
        )

        # Calculate cost
        cost = llm_service.calculate_cost(
            model=request.model,
            prompt_tokens=completion["usage"]["prompt_tokens"],
            completion_tokens=completion["usage"]["completion_tokens"]
        )

        # Save to database if conversation_id provided
        if request.conversation_id:
            await save_message_to_db(
                conversation_id=request.conversation_id,
                role="assistant",
                content=completion["content"],
                model=request.model,
                prompt_tokens=completion["usage"]["prompt_tokens"],
                completion_tokens=completion["usage"]["completion_tokens"],
                cost=cost,
                db=db
            )

        # Cache the response
        if settings.semantic_cache_enabled:
            await cache_service.cache_response(
                messages=messages,
                model=request.model,
                response=completion
            )

        return ChatResponse(
            id=completion["id"],
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=completion["content"]
                    ),
                    finish_reason=completion["finish_reason"]
                )
            ],
            usage=ChatUsage(
                prompt_tokens=completion["usage"]["prompt_tokens"],
                completion_tokens=completion["usage"]["completion_tokens"],
                total_tokens=completion["usage"]["total_tokens"],
                estimated_cost=cost
            )
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating completion: {str(e)}"
        )


async def stream_chat_response(
    messages: list,
    model: str,
    temperature: float,
    max_tokens: int,
    user: User,
    conversation_id: str,
    db: Session
) -> AsyncIterator[str]:
    """Stream chat response in SSE format"""

    try:
        full_response = ""
        prompt_tokens = 0
        completion_tokens = 0

        # Stream tokens
        async for token in llm_service.stream_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            full_response += token
            completion_tokens += 1

            # Format as SSE
            chunk_data = {
                "id": f"chatcmpl-{uuid.uuid4()}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": token},
                    "finish_reason": None
                }]
            }

            yield f"data: {json.dumps(chunk_data)}\n\n"

        # Send final chunk
        final_chunk = {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }

        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"

        # Save to database
        if conversation_id:
            # Estimate prompt tokens
            prompt_tokens = sum(len(m["content"].split()) * 1.3 for m in messages)

            cost = llm_service.calculate_cost(
                model=model,
                prompt_tokens=int(prompt_tokens),
                completion_tokens=completion_tokens
            )

            await save_message_to_db(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
                model=model,
                prompt_tokens=int(prompt_tokens),
                completion_tokens=completion_tokens,
                cost=cost,
                db=db
            )

    except Exception as e:
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "internal_error"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"


async def save_message_to_db(
    conversation_id: str,
    role: str,
    content: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost: float,
    db: Session
):
    """Save message to database"""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        estimated_cost=cost
    )

    db.add(message)
    db.commit()


@router.get("/models")
async def list_models(current_user: User = Depends(get_current_user)):
    """List available models"""
    models = []

    # OpenAI models
    if settings.openai_api_key:
        models.extend([
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "openai"},
        ])

    # Anthropic models
    if settings.anthropic_api_key:
        models.extend([
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "provider": "anthropic"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "provider": "anthropic"},
        ])

    # Ollama models (always available)
    models.extend([
        {"id": "llama3.1:8b", "name": "Llama 3.1 8B", "provider": "ollama"},
        {"id": "llama3.1:70b", "name": "Llama 3.1 70B", "provider": "ollama"},
    ])

    return {"models": models}
