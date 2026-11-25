"""CodeAtlas REST API. Run with uvicorn codeatlas.api.app:app."""

import hmac
import time
from collections import deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from codeatlas.agents.service import CodeAtlasAgent
from codeatlas.analysis.repository import analyze, change_impact
from codeatlas.api.schemas import ImportRequest, QuestionRequest
from codeatlas.api.service import RepositoryService
from codeatlas.config import settings
from codeatlas.indexing.vector_store import VectorStore
from codeatlas.rag import CodeRAG
from codeatlas.retrieval.hybrid import HybridRetriever
from codeatlas.tools.registry import ToolRegistry
from codeatlas.tools.repository_tools import RepositoryTools


def create_app(service: RepositoryService | None = None) -> FastAPI:
    service = service or RepositoryService()

    @asynccontextmanager
    async def lifespan(app):
        if settings.environment == "production" and len(settings.api_token) < 32:
            raise RuntimeError("Production requires API_TOKEN with at least 32 characters.")
        yield
        service.executor.shutdown(wait=True, cancel_futures=True)

    app = FastAPI(title="CodeAtlas", version="0.2.0", lifespan=lifespan)
    app.state.service = service
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    requests = deque()

    @app.middleware("http")
    async def guard(request: Request, call_next):
        if request.url.path not in {"/health", "/docs", "/openapi.json"}:
            if settings.api_token and not hmac.compare_digest(
                request.headers.get("authorization", ""), f"Bearer {settings.api_token}"
            ):
                return JSONResponse({"error": {"code": "unauthorized"}}, status_code=401)
            now = time.monotonic()
            while requests and requests[0] < now - 60:
                requests.popleft()
            if len(requests) >= settings.api_requests_per_minute:
                return JSONResponse(
                    {"error": {"code": "rate_limit"}},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
            requests.append(now)
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 32768:
                    return JSONResponse({"error": {"code": "body_too_large"}}, status_code=413)
            request._body = bytes(body)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return JSONResponse(
            {"error": {"code": str(exc.status_code), "message": str(exc.detail)}},
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse(
            {"error": {"code": "validation", "message": "Invalid request."}}, status_code=422
        )

    @app.exception_handler(Exception)
    async def unexpected(request, exc):
        return JSONResponse(
            {
                "error": {
                    "code": "unavailable",
                    "message": "Operation unavailable; check providers.",
                }
            },
            status_code=503,
        )

    def tools(identifier):
        try:
            return RepositoryTools(service.repository(identifier))
        except KeyError as exc:
            raise HTTPException(404, "Repository not found.") from exc

    @app.get("/health")
    def health():
        return {"status": "ok", "version": "0.2.0"}

    @app.get("/api/readiness")
    def readiness():
        # Configuration readiness is distinct from successful provider inference.
        return {
            "embedding_provider": settings.llm_provider,
            "chat_provider": settings.chat_provider or settings.llm_provider,
            "chat_configured": bool(
                settings.groq_api_key
                if settings.chat_provider == "groq"
                else settings.openai_api_key
                if settings.chat_provider == "openai"
                else True
            ),
            "inference_verified": False,
        }

    @app.get("/api/repositories")
    def repositories():
        return service.list()

    @app.post("/api/repositories", status_code=202)
    def import_repository(body: ImportRequest):
        try:
            return service.submit(body.url)
        except RuntimeError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/api/jobs/{identifier}")
    def job(identifier: str):
        with service.lock:
            if identifier not in service.jobs:
                raise HTTPException(404, "Job not found; jobs expire on restart.")
            return dict(service.jobs[identifier])

    @app.get("/api/repositories/{identifier}/tree")
    def tree(identifier: str):
        return {"files": sorted(tools(identifier).file_map)}

    @app.get("/api/repositories/{identifier}/overview")
    def overview(identifier: str):
        return analyze(tools(identifier))

    @app.get("/api/repositories/{identifier}/impact")
    def impact(identifier: str):
        repository_tools = tools(identifier)
        return change_impact(repository_tools, analyze(repository_tools))

    @app.get("/api/repositories/{identifier}/source")
    def source(identifier: str, path: str = Query(max_length=500), start: int = Query(1, ge=1)):
        try:
            repository_tools = tools(identifier)
            return {
                **repository_tools.read_file(path, start, start + 119),
                **repository_tools.get_dependencies(path),
            }
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/repositories/{identifier}/questions")
    def question(identifier: str, body: QuestionRequest):
        repository_tools = tools(identifier)
        if not service.compute.acquire(blocking=False):
            raise HTTPException(409, "An AI or indexing operation is already running.")
        try:
            retriever = HybridRetriever(VectorStore(identifier))
            if body.mode == "agent":
                repository_tools.retriever = retriever
                return CodeAtlasAgent(ToolRegistry(repository_tools)).investigate(body.question)
            return CodeRAG(retriever).ask(body.question, [m.model_dump() for m in body.history])
        finally:
            service.compute.release()

    @app.delete("/api/repositories/{identifier}")
    def remove(identifier: str):
        tools(identifier)
        if not service.compute.acquire(blocking=False):
            raise HTTPException(409, "An operation is already running.")
        try:
            service.remove(identifier)
            return {"removed": True}
        finally:
            service.compute.release()

    return app


app = create_app()
