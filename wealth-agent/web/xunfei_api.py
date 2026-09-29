from fastapi import HTTPException, APIRouter, UploadFile, File, Form
from services.xunfei_iat import recognize_speech
from pydantic import BaseModel
from config import get_project_client_config

xunfei_router = APIRouter(prefix="/api/xunfei")


class IATResponse(BaseModel):
    code: int
    message: str
    data: str


@xunfei_router.post("/iat", response_model=IATResponse)
async def speech_to_text(
    audio: UploadFile = File(...), language: str = Form("zh_cn"), accent: str = Form("mandarin")
):
    try:
        audio_data = await audio.read(2 * 1024 * 1024 + 1)
        if not audio_data or len(audio_data) > 2 * 1024 * 1024:
            raise HTTPException(413, "Audio must contain at most 2 MiB")
        result = await recognize_speech(
            app_id=get_project_client_config("xunfei", "app_id"),
            api_key=get_project_client_config("xunfei", "api_key"),
            api_secret=get_project_client_config("xunfei", "api_secret"),
            audio_data=audio_data,
            language=language,
            accent=accent,
        )
        return IATResponse(code=0, message="success", data=result)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(502, "Speech service unavailable") from None
