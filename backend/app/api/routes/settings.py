from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class LLMKeyRequest(BaseModel):
    api_key: str


@router.post("/llm-key")
async def set_llm_key(req: LLMKeyRequest):
    from app.llm import llm_router
    llm_router.update_provider_key("zen", req.api_key)
    return {"success": True, "provider": "zen", "configured": True}
