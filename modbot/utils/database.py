from __future__ import annotations

import enum

import asyncpg
import ulid

__all__ = ("ModAction", "add_custom_enum", "database_hook", "generate_id")

class ModAction(enum.Enum):
    kick = "kick"
    ban = "ban"
    timeout = "timeout"
    warn = "warn"


async def add_custom_enum(
    pool: asyncpg.pool.PoolConnectionProxy[asyncpg.Record],
    name: str,
    enun: type[enum.Enum],
):
    await pool.set_type_codec(name, encoder=lambda e: e.name, decoder=enun)


async def database_hook(pool: asyncpg.pool.PoolConnectionProxy[asyncpg.Record]):
    await add_custom_enum(pool, "mod_action", ModAction)


def generate_id() -> str:
    return ulid.new().str
