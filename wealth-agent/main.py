import os
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from web.agent_api import agent_router

from config import get_configuration
from contextlib import asynccontextmanager
from util.clients import init_http_clients, close_http_clients
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_http_clients()
    try:
        yield
    finally:
        await close_http_clients()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(agent_router)
if os.getenv("ENABLE_SPEECH", "false").lower() == "true":
    from web.xunfei_api import xunfei_router

    app.include_router(xunfei_router)
app_configuration = get_configuration("application", "app")


@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    # Pydantic's default error payload includes the rejected value, possibly a token.
    errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})


@app.get("/healthz")
def health():
    from config import external_services_enabled

    return {"status": "ok", "external_services_enabled": external_services_enabled()}


if __name__ == "__main__":
    uvicorn.run(app, host=app_configuration["host"], port=app_configuration["port"])
