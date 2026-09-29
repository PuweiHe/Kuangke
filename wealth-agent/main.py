import os
import uvicorn
from fastapi import FastAPI
from web.agent_api import agent_router

from util.requests_log_util import apply_request_logging
from config import get_configuration
from contextlib import asynccontextmanager
from util.clients import init_http_clients, close_http_clients
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_http_clients()
    yield
    await close_http_clients()
app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000'], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])
app.include_router(agent_router)
if os.getenv("ENABLE_SPEECH", "false").lower() == "true":
    from web.xunfei_api import xunfei_router
    app.include_router(xunfei_router)
app_configuration = get_configuration('application', 'app')

if __name__ == "__main__":
    uvicorn.run(app, host=app_configuration["host"], port=app_configuration["port"])
