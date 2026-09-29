from fastapi import APIRouter, UploadFile, File, Form
from services.xunfei_iat import recognize_speech
from pydantic import BaseModel
from config import get_project_client_config
xunfei_router = APIRouter(prefix='/api/xunfei')

class IATResponse(BaseModel):
    code: int
    message: str
    data: str

@xunfei_router.post('/iat', response_model=IATResponse)
async def speech_to_text(audio: UploadFile=File(...), language: str=Form('zh_cn'), accent: str=Form('mandarin')):
    try:
        audio_data = await audio.read()
        result = await recognize_speech(app_id=get_project_client_config('xunfei', 'app_id'), api_key=get_project_client_config('xunfei', 'api_key'), api_secret=get_project_client_config('xunfei', 'api_secret'), audio_data=audio_data, language=language, accent=accent)
        return IATResponse(code=0, message='success', data=result)
    except Exception as e:
        return IATResponse(code=500, message=str(e), data='')
