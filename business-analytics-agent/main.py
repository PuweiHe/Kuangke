import uvicorn
from fastapi import FastAPI
from web.agent_api import agent_router
from util.requests_log_util import apply_request_logging
from config import get_configuration
app = FastAPI()
app.include_router(agent_router)
apply_request_logging()
app_configuration = get_configuration('application', 'app')

if __name__ == "__main__":
    uvicorn.run(app, host=app_configuration["host"], port=app_configuration["port"])
