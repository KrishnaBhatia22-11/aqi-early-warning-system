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


@router.get("/db/all")
async def db_all():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AQIReading.city, AQIReading.aqi, AQIReading.pm25,
                       AQIReading.timestamp, AQIReading.source)
                .order_by(AQIReading.timestamp.desc())
            )
            rows = result.all()
        return [
            {
                "city":      r.city,
                "aqi":       r.aqi,
                "pm25":      r.pm25,
                "timestamp": r.timestamp.isoformat(),
                "source":    r.source,
            }
            for r in rows
        ]
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/db/cleanup")
async def db_cleanup():
    """
    Delete known-bad historical rows caused by stale data, foreign stations,
    and city mismatches that were stored before the validation fixes.
    """
    try:
        async with AsyncSessionLocal() as session:
            r_pune = await session.execute(
                text("DELETE FROM aqi_readings WHERE city = 'Pune' AND aqi > 150")
            )
            r_raipur = await session.execute(
                text("DELETE FROM aqi_readings WHERE city = 'Raipur'")
            )
            r_kochi = await session.execute(
                text("DELETE FROM aqi_readings WHERE city = 'Kochi'")
            )
            r_ranchi = await session.execute(
                text("DELETE FROM aqi_readings WHERE city = 'Ranchi'")
            )
            r_chandigarh = await session.execute(
                text("DELETE FROM aqi_readings WHERE city = 'Chandigarh' AND aqi > 200")
            )
            await session.commit()

        deleted = {
            "Pune":           r_pune.rowcount,
            "Raipur":         r_raipur.rowcount,
            "Kochi":          r_kochi.rowcount,
            "Ranchi":         r_ranchi.rowcount,
            "Chandigarh_bad": r_chandigarh.rowcount,
        }
        total = sum(deleted.values())
        return {"cleaned": True, "deleted": deleted, "total_deleted": total}
    except Exception as e:
        return {"cleaned": False, "error": str(e)}
