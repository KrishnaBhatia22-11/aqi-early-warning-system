from fastapi import APIRouter
from sqlalchemy import text
from api.database import AsyncSessionLocal

router = APIRouter()


@router.get("/db/status")
async def db_status():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM aqi_readings"))
            row_count = result.scalar()
        return {"status": "connected", "table": "aqi_readings", "row_count": row_count}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
