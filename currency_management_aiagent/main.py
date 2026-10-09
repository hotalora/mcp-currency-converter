# main.py
import asyncio
import os
from contextlib import asynccontextmanager
from functools import partial

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
from dependency_injector.wiring import inject, Provide

from application.settings.container import Container
from application.settings.settings import Config
from domain.model.agent_message import AgentRequest
from domain.usecase.process_agent_message_use_case import (
    ProcessAgentMessageUseCase
)
from infrastructure.entry_points.api.dto.chat_request import (
    ChatRequest,
    ChatResponse,
)
from infrastructure.helpers.logger_helper import setup_logging
# --- BEGIN OTEL_IMPORT ---
from infrastructure.helpers.open_telemetry import activate_open_telemetry
# --- END OTEL_IMPORT ---
from infrastructure.helpers.check_connectivity import check_connectivity

import logging

logger = logging.getLogger(__name__)

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


@router.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
@inject
async def chat(
    body: ChatRequest,
    http_request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    use_case: ProcessAgentMessageUseCase = Depends(
        Provide[Container.process_agent_message_use_case]
    ),
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="A bearer access token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    authorization = f"Bearer {credentials.credentials}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            auth_response = await client.get(
                http_request.app.state.container.config.auth_provider_url(),
                headers={"Authorization": authorization},
            )
    except httpx.RequestError as error:
        logger.error("Auth provider request failed: %s", error)
        raise HTTPException(
            status_code=503,
            detail="Authentication service is unavailable.",
        ) from error
    if auth_response.status_code == 401:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if auth_response.status_code != 200:
        raise HTTPException(
            status_code=503,
            detail="Authentication service returned an unexpected response.",
        )
    try:
        auth_result = auth_response.json()
    except ValueError as error:
        raise HTTPException(
            status_code=503,
            detail="Authentication service returned invalid JSON.",
        ) from error
    if (
        not isinstance(auth_result, dict)
        or auth_result.get("valid") is not True
        or not isinstance(auth_result.get("user"), dict)
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    agent_request = AgentRequest(
        conversation_id=body.conversation_id or "default",
        user_message=body.message,
        metadata={
            "UserIdentifier": body.conversation_id or "default",
            "ApplicationIdentifier": "default",
            "Authorization": authorization,
        },
    )
    response = await use_case.execute(agent_request)
    if response.status == "error":
        raise HTTPException(status_code=500, detail=response.error_message)
    return {
        "conversation_id": response.conversation_id,
        "messages": [
            {"type": msg.type, "content": msg.content}
            for msg in response.agent_response
        ],
    }


@asynccontextmanager
async def lifespan(_: FastAPI, container: Container):
    """Manage IoC container and application lifespan."""
    await check_connectivity(
        enabled=container.config.check_connectivity_on_startup()
    )

    # --- BEGIN VALKEY_LIFESPAN ---
    cache_repository = container.cache_repository()
    await cache_repository.initialize()
    # --- END VALKEY_LIFESPAN ---

    yield

    shutdown = container.shutdown_resources()
    if shutdown is not None:
        await shutdown


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    container = Container()
    container.config.from_pydantic(Config())
    container.wire(modules=[__name__])

    setup_logging(container.config.logger())
    # --- BEGIN OTEL_ACTIVATE ---
    activate_open_telemetry()
    # --- END OTEL_ACTIVATE ---

    app = FastAPI(
        title="Agent Service",
        lifespan=partial(lifespan, container=container),
    )
    app.state.container = container

    app.include_router(router)

    return app


app = create_application()

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", "8003"))
    uvicorn.run(app, host="0.0.0.0", port=port)