import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy import text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Normalize for asyncpg driver
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create engine & session factory
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def db_ping():
    """Simple health check for DB connection"""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


DDL = r"""
CREATE TABLE IF NOT EXISTS exchanges (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS pairs (
  id SERIAL PRIMARY KEY,
  symbol TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS ticks (
  id BIGSERIAL PRIMARY KEY,
  exchange_id INT NOT NULL REFERENCES exchanges(id),
  pair_id INT NOT NULL REFERENCES pairs(id),
  price NUMERIC(18,8) NOT NULL,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ticks_pair_time ON ticks(pair_id, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_ticks_exchange_time ON ticks(exchange_id, fetched_at DESC);

CREATE TABLE IF NOT EXISTS opportunities (
  id BIGSERIAL PRIMARY KEY,
  pair_id INT NOT NULL REFERENCES pairs(id),
  buy_exchange_id INT NOT NULL REFERENCES exchanges(id),
  sell_exchange_id INT NOT NULL REFERENCES exchanges(id),
  diff_abs NUMERIC(18,8) NOT NULL,
  diff_pct NUMERIC(9,6) NOT NULL,
  est_profit_usd NUMERIC(18,8),
  detected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_opps_pair_time ON opportunities(pair_id, detected_at DESC);

CREATE TABLE IF NOT EXISTS alerts_sent (
  id BIGSERIAL PRIMARY KEY,
  opportunity_id BIGINT NOT NULL REFERENCES opportunities(id),
  chat_id TEXT,
  ok BOOLEAN NOT NULL,
  sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  error TEXT
);
CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts_sent(sent_at DESC);

-- Prepopulate static data
INSERT INTO exchanges(name) VALUES ('Nobitex') ON CONFLICT DO NOTHING;
INSERT INTO exchanges(name) VALUES ('Wallex') ON CONFLICT DO NOTHING;
INSERT INTO pairs(symbol) VALUES ('BTCUSDT') ON CONFLICT DO NOTHING;
"""


async def init_db_schema():
    """Create tables and indexes if not exist"""
    async with engine.begin() as conn:
        for stmt in filter(None, DDL.split(';')):
            sql = stmt.strip()
            if sql:
                await conn.execute(text(sql))
    print("✅ Database schema initialized.")


async def _get_id(conn, table: str, name_col: str, name_val: str) -> int:
    """Return ID of a record, inserting if not present."""
    row = await conn.execute(
        text(f"SELECT id FROM {table} WHERE {name_col}=:v LIMIT 1"),
        {"v": name_val},
    )
    r = row.first()
    if r:
        return r[0]

    row = await conn.execute(
        text(
            f"INSERT INTO {table}({name_col}) VALUES(:v) "
            "ON CONFLICT DO NOTHING RETURNING id"
        ),
        {"v": name_val},
    )
    r = row.first()
    if r:
        return r[0]

    row = await conn.execute(
        text(f"SELECT id FROM {table} WHERE {name_col}=:v LIMIT 1"),
        {"v": name_val},
    )
    return row.first()[0]


async def save_tick(exchange_name: str, pair_symbol: str, price: float):
    """Store latest tick price"""
    async with SessionLocal() as s:
        async with s.begin():
            ex_id = await _get_id(s, "exchanges", "name", exchange_name)
            pr_id = await _get_id(s, "pairs", "symbol", pair_symbol)
            await s.execute(
                text(
                    "INSERT INTO ticks(exchange_id, pair_id, price) "
                    "VALUES(:e,:p,:pr)"
                ),
                {"e": ex_id, "p": pr_id, "pr": price},
            )


async def save_opportunity(
    pair_symbol: str,
    buy_ex: str,
    sell_ex: str,
    diff_abs: float,
    diff_pct: float,
    est_profit_usd: float | None = None,
) -> int:
    """Store arbitrage opportunity and return its ID"""
    async with SessionLocal() as s:
        async with s.begin():
            pr_id = await _get_id(s, "pairs", "symbol", pair_symbol)
            buy_id = await _get_id(s, "exchanges", "name", buy_ex)
            sell_id = await _get_id(s, "exchanges", "name", sell_ex)
            res = await s.execute(
                text(
                    """
                    INSERT INTO opportunities(
                        pair_id, buy_exchange_id, sell_exchange_id,
                        diff_abs, diff_pct, est_profit_usd
                    )
                    VALUES(:p,:b,:s,:da,:dp,:ep)
                    RETURNING id
                    """
                ),
                {
                    "p": pr_id,
                    "b": buy_id,
                    "s": sell_id,
                    "da": diff_abs,
                    "dp": diff_pct,
                    "ep": est_profit_usd,
                },
            )
            return res.scalar_one()

if __name__ == "__main__":
    asyncio.run(init_db_schema())
