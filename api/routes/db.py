from fastapi import APIRouter
from sqlalchemy import text, select
from api.database import AsyncSessionLocal
from api.models import AQIReading

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


@router.get("/db/latest")
async def db_latest():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AQIReading.city, AQIReading.aqi, AQIReading.timestamp)
                .order_by(AQIReading.timestamp.desc())
                .limit(5)
            )
            rows = result.all()
        return [
            {"city": r.city, "aqi": r.aqi, "timestamp": r.timestamp.isoformat()}
            for r in rows
        ]
    except Exception as e:
        return {"status": "error", "detail": str(e)}
