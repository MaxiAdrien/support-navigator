import json
from collections.abc import Iterator
from typing import Literal
from uuid import uuid4

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from structlog.contextvars import bind_contextvars, clear_contextvars

from config import API_ALLOWED_ORIGINS, CHAT_RATE_LIMIT
from app.graph import app as graph_app
from app.logging_config import configure_logging


# Set-up
load_dotenv()
configure_logging()
logger = structlog.get_logger('support_navigator.api')
app = FastAPI(title='Support Navigator API')

# Configure CORS middleware to allow requests from specified origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['*'],
)

# Configure rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class ChatMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)


def build_messages(history: list[ChatMessage], query: str) -> list[BaseMessage]:
    """Build a list of BaseMessage objects from the conversation history and the current query."""

    messages: list[BaseMessage] = []

    for item in history:
        if item.role == 'user':
            messages.append(HumanMessage(content=item.content))
        else:
            messages.append(AIMessage(content=item.content))

    messages.append(HumanMessage(content=query))

    return messages


def generate_chat_stream(messages: list[BaseMessage]) -> Iterator[str]:
    """Generator function to stream chat responses from the graph."""

    # Initialise answer and state
    answer, state = '', {}

    # Stream from the graph
    try:
        for mode, item in graph_app.stream({'messages': messages}, stream_mode=['custom', 'values']):

            # Answer tokens
            if mode == 'custom':
                delta = str(item)
                answer += delta
                yield json.dumps({'type': 'token', 'content': delta}, ensure_ascii=False) + '\n'

            # Graph state
            elif mode == 'values':
                state = item

        # Response payload
        payload = {
            'type': 'final',
            'rewritten_query': state.get('rewritten_query', ''),
            'documents': state.get('documents', []),
        }

        # Log stream completed
        logger.info('chat_stream_completed', answer_chars=len(answer), docs=len(payload['documents']))

        yield json.dumps(payload, ensure_ascii=False) + '\n'

    except Exception:
        logger.exception('chat_stream_failed')
        yield json.dumps({'type': 'error', 'message': 'The assistant service failed to generate a response.'}, ensure_ascii=False) + '\n'


@app.get('/health')
def health() -> dict[str, str]:
    """Health check endpoint to verify that the API is running."""
    return {'status': 'ok'}


@app.post('/chat/stream')
@limiter.limit(CHAT_RATE_LIMIT)
def chat_stream(request: Request, chat_request: ChatRequest) -> StreamingResponse:
    """
    Stream a chat response based on the user's query and conversation history.
    Note: "request: Request" argument is required for SlowAPI rate limiter.
    """

    # Generate unique request ID for logging
    request_id = str(uuid4())
    clear_contextvars()
    bind_contextvars(request_id=request_id)

    # Log user query
    logger.info('user_query_received', chars=len(chat_request.query), preview=chat_request.query[:120])

    # Build messages from history and current query
    messages = build_messages(chat_request.history, chat_request.query)

    # Stream chat response from graph
    return StreamingResponse(generate_chat_stream(messages), media_type='application/x-ndjson')
