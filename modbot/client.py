from __future__ import annotations


import logging
import pathlib
from types import new_class
from typing import Literal, MutableMapping, Self

import aiohttp
import lru
import revolt
from asyncpg import Pool, Record
from revolt.ext import commands

from .utils import Config, ModAction


class Client(commands.CommandsClient):
    def __init__(
        self, config: Config, session: aiohttp.ClientSession, database: Pool[Record]
    ):
        super().__init__(session, config.bot.token, case_insensitive=True)

        self.database = database
        self.config = config

        self.prefixes: MutableMapping[str, str] = lru.LRU(500)
        self.log_channels: MutableMapping[str, str] = lru.LRU(500)

        misc = new_class("Misc", (commands.Cog[Self],))()

        self.add_cog(misc)

        help_command = self.get_command("help")
        help_command.cog = misc

        self.load_extensions()


    async def get_server_prefix(self, server_id: str) -> str:
        if not (prefix := self.prefixes.get(server_id)):
            async with self.database.acquire() as conn:
                custom_prefix = await conn.fetchval(
                    "select prefix from server_configs where server_id=$1", server_id
                )

                self.prefixes[server_id] = prefix = (
                    custom_prefix or self.config.bot.default_prefix
                )

        return prefix

    async def get_server_log_channel(self, server_id: str) -> str | None:
        if not (log_channel := self.prefixes.get(server_id)):
            async with self.database.acquire() as conn:
                log_channel = await conn.fetchval(
                    "select log_channel from server_configs where server_id=$1",
                    server_id,
                )

                self.log_channels[server_id] = log_channel

        return log_channel

    async def get_prefix(self, message: revolt.Message) -> list[str]:
        if server_id := message.channel.server_id:
            custom_prefix = await self.get_server_prefix(server_id)
        else:
            custom_prefix = "-"

        return [f"<@{self.user.id}> ", f"<@{self.user.id}>", custom_prefix]

    def load_extensions(self):
        modbot = pathlib.Path.cwd() / "modbot"
        cogs = modbot / "cogs"

        for path in cogs.iterdir():
            if path.stem.startswith("_") or path.suffix != ".py":
                continue

            self.load_extension(f"modbot.cogs.{path.stem}")

    def get_context(self, message: revolt.Message) -> type[Context]:
        return Context

    async def on_ready(self):
        logging.info("Ready")
        logging.info("Logged into %s", self.user.name)


class Context(commands.Context[Client]):
    async def embed_send(
        self, content: str, *, status: Literal["ok", "fail"] = "ok"
    ) -> revolt.Message:
        avatar = self.client.user.avatar
        assert avatar is not None

        return await self.send(
            embed=revolt.SendableEmbed(
                icon_url=avatar.url, title="Moderation Bot", description=content
            )
        )
