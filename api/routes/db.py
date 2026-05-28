import re
from fastapi import APIRouter, Query, Request, HTTPException
from sqlalchemy import text, select
from datetime import datetime, timezone, timedelta
from api.database import AsyncSessionLocal
from api.models import AQIReading
from config.settings import CITY_COORDS
from api.limiter import limiter

router = APIRouter()

_CITY_RE = re.compile(r'^[A-Za-z][A-Za-z \-]{0,49}$')


def _validate_city(name: str):
    if not name or len(name) > 50:
        raise HTTPException(status_code=400, detail="City name must be 1–50 characters")
    if not _CITY_RE.match(name):
        raise HTTPException(
            status_code=400,
            detail="City name may only contain letters, spaces, and hyphens",
        )


@router.get("/db/status")
@limiter.limit("10/minute")
async def db_status(request: Request):
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


@router.get("/db/history")
@limiter.limit("20/minute")
async def db_history(
    request: Request,
    city: str = Query(default="Delhi"),
    days: int = Query(default=7, ge=1, le=12),
):
    _validate_city(city)
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        async with AsyncSessionLocal() as session:
            rows = (await session.execute(
                select(
                    AQIReading.timestamp, AQIReading.aqi,
                    AQIReading.pm25, AQIReading.pm10, AQIReading.no2,
                    AQIReading.co, AQIReading.so2, AQIReading.o3,
                )
                .where(AQIReading.city == city, AQIReading.timestamp >= cutoff)
                .order_by(AQIReading.timestamp.asc())
            )).all()

        if not rows:
            return {"city": city, "days": days, "readings": [], "summary": None}

        def _r(v, n=1):
            return round(v, n) if v is not None else None

        readings = [
            {
                "timestamp": r.timestamp.isoformat(),
                "aqi":  round(r.aqi) if r.aqi is not None else None,
                "pm25": _r(r.pm25),
                "pm10": _r(r.pm10),
                "no2":  _r(r.no2),
                "co":   _r(r.co),
                "so2":  _r(r.so2),
                "o3":   _r(r.o3),
            }
            for r in rows
        ]

        aqis    = [rd["aqi"] for rd in readings if rd["aqi"] is not None]
        max_row = max(rows, key=lambda r: r.aqi or 0)
        min_row = min(rows, key=lambda r: r.aqi if r.aqi is not None else 9999)

        return {
            "city":     city,
            "days":     days,
            "readings": readings,
            "summary":  {
                "avg_aqi":        round(sum(aqis) / len(aqis)) if aqis else None,
                "max_aqi":        round(max_row.aqi) if max_row.aqi is not None else None,
                "min_aqi":        round(min_row.aqi) if min_row.aqi is not None else None,
                "max_aqi_time":   max_row.timestamp.isoformat(),
                "min_aqi_time":   min_row.timestamp.isoformat(),
                "total_readings": len(readings),
            },
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/db/audit")
async def db_audit():
    try:
        async with AsyncSessionLocal() as session:
            total = (await session.execute(
                text("SELECT COUNT(*) FROM aqi_readings")
            )).scalar()

            date_row = (await session.execute(
                text("SELECT MIN(timestamp), MAX(timestamp) FROM aqi_readings")
            )).one()
            earliest = date_row[0].isoformat() if date_row[0] else None
            latest   = date_row[1].isoformat() if date_row[1] else None

            per_city_rows = (await session.execute(
                text("SELECT city, COUNT(*) FROM aqi_readings GROUP BY city")
            )).all()
            db_counts = {row[0]: row[1] for row in per_city_rows}

            aqi_null     = (await session.execute(text("SELECT COUNT(*) FROM aqi_readings WHERE aqi IS NULL"))).scalar()
            aqi_zero     = (await session.execute(text("SELECT COUNT(*) FROM aqi_readings WHERE aqi = 0"))).scalar()
            aqi_too_low  = (await session.execute(text("SELECT COUNT(*) FROM aqi_readings WHERE aqi < 5"))).scalar()
            aqi_too_high = (await session.execute(text("SELECT COUNT(*) FROM aqi_readings WHERE aqi > 500"))).scalar()

        rows_per_city       = {city: db_counts.get(city, 0) for city in CITY_COORDS}
        cities_with_no_data = [city for city, n in rows_per_city.items() if n == 0]

        return {
            "total_rows": total,
            "date_range": {
                "earliest": earliest,
                "latest":   latest,
            },
            "rows_per_city": rows_per_city,
            "suspicious_rows": {
                "aqi_null":            aqi_null,
                "aqi_zero":            aqi_zero,
                "aqi_too_low":         aqi_too_low,
                "aqi_too_high":        aqi_too_high,
                "cities_with_no_data": cities_with_no_data,
            },
        }
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
            r_surat = await session.execute(
                text("DELETE FROM aqi_readings WHERE city = 'Surat'")
            )
            r_aurangabad = await session.execute(
                text("DELETE FROM aqi_readings WHERE city = 'Aurangabad'")
            )
            r_invalid_aqi = await session.execute(
                text("DELETE FROM aqi_readings WHERE aqi > 500")
            )
            await session.commit()

        deleted = {
            "Pune":           r_pune.rowcount,
            "Raipur":         r_raipur.rowcount,
            "Kochi":          r_kochi.rowcount,
            "Ranchi":         r_ranchi.rowcount,
            "Chandigarh_bad": r_chandigarh.rowcount,
            "Surat":          r_surat.rowcount,
            "Aurangabad":     r_aurangabad.rowcount,
            "invalid_aqi":    r_invalid_aqi.rowcount,
        }
        total = sum(deleted.values())
        return {"cleaned": True, "deleted": deleted, "total_deleted": total}
    except Exception as e:
        return {"cleaned": False, "error": str(e)}
