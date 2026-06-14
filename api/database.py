import os
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base


def _normalize_database_url(raw_url: str) -> tuple[str, dict]:
    """Normalize DATABASE_URL for the asyncpg driver.

    Returns ``(url, connect_args)`` and works for both the old Render-style URL
    and a fresh Neon URL (``...?sslmode=require``):

    - ``postgresql://`` / ``postgres://`` -> ``postgresql+asyncpg://`` so
      SQLAlchemy uses the async asyncpg driver.
    - Strips libpq-only query params (``sslmode``, ``channel_binding``) that
      asyncpg does NOT accept as URL params (unlike psycopg2).
    - If the URL requested SSL (e.g. Neon's ``sslmode=require``), TLS is enabled
      explicitly via ``connect_args={"ssl": True}`` — the way asyncpg wants it.
    - If there's no sslmode at all (local/Render), connect_args stays empty so
      nothing breaks.
    """
    if not raw_url:
        return raw_url, {}

    # Use the asyncpg driver regardless of which postgres scheme was supplied.
    if raw_url.startswith("postgresql://"):
        raw_url = "postgresql+asyncpg://" + raw_url[len("postgresql://"):]
    elif raw_url.startswith("postgres://"):
        raw_url = "postgresql+asyncpg://" + raw_url[len("postgres://"):]

    split = urlsplit(raw_url)
    connect_args: dict = {}
    kept_pairs = []

    for key, value in parse_qsl(split.query, keep_blank_values=True):
        lkey = key.lower()
        if lkey == "sslmode":
            # Translate libpq sslmode -> asyncpg ssl. Anything other than
            # "disable"/"allow" means TLS is expected (Neon uses "require").
            if value.lower() not in ("disable", "allow"):
                connect_args["ssl"] = True
        elif lkey == "channel_binding":
            # asyncpg-incompatible libpq param — drop it.
            continue
        else:
            kept_pairs.append((key, value))

    normalized = urlunsplit(
        (split.scheme, split.netloc, split.path, urlencode(kept_pairs), split.fragment)
    )
    return normalized, connect_args


DATABASE_URL, _CONNECT_ARGS = _normalize_database_url(os.environ.get("DATABASE_URL", ""))

# Neon's free tier prefers small pools; pool_pre_ping recycles connections that
# went stale after Neon auto-suspends an idle compute, instead of erroring.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    pool_pre_ping=True,
    connect_args=_CONNECT_ARGS,
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
