from fastapi import APIRouter

router = APIRouter()

@router.get("/auth")
async def auth():
    return {"message": "This is the auth route"}