import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from web.agent_api import agent_router
from config import get_configuration

app = FastAPI()
app.include_router(agent_router)
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
