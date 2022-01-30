from fastapi import APIRouter
from models import Guild

router = APIRouter()


@router.get("/isprime")
async def read_items(guild_id: int):
    return await Guild.filter(pk=guild_id, is_premium=True).exists()
