import asyncio

import asyncpg
import revolt
import logging

from .client import Client
from .utils import database_hook, load_config

logging.basicConfig(level=logging.DEBUG)

async def main():
    config = load_config()

    async with revolt.utils.client_session() as session, asyncpg.create_pool(
        config.database.uri, setup=database_hook
    ) as database:
        client = Client(config, session, database)

        await client.start()


asyncio.run(main())
