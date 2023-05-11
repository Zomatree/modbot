import argparse
import asyncio

import asyncpg
import revolt
import logging

from .client import Client
from .utils import database_hook, load_config


parser = argparse.ArgumentParser()
parser.add_argument("config", help="config file for the bot")

async def main():
    args = parser.parse_args()

    config = load_config(args.config)
    logging.basicConfig(level=logging.DEBUG)

    async with revolt.utils.client_session() as session, asyncpg.create_pool(
        config.database.uri, setup=database_hook
    ) as database:
        client = Client(config, session, database)

        await client.start()


asyncio.run(main())
