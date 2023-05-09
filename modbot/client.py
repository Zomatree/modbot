from __future__ import annotations


import logging
import pathlib
from types import new_class
from typing import Literal, Self

import aiohttp
import lru
import revolt
from asyncpg import Pool, Record
from revolt.ext import commands

from .utils import Config

class Client(commands.CommandsClient):
    def __init__(
        self, config: Config, session: aiohttp.ClientSession, database: Pool[Record]
    ):
        super().__init__(session, config.bot.token, case_insensitive=True)

        self.database = database
        self.config = config

        self.prefixes: lru.LRU[str, str] = lru.LRU(500)
        self.log_channels: lru.LRU[str, str] = lru.LRU(500)

        self.reaction_role_messages: lru.LRU[str, bool] = lru.LRU(500)

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
            custom_prefix = self.config.bot.default_prefix

        return [f"<@{self.user.id}> ", f"<@{self.user.id}>", custom_prefix]

    def load_extensions(self):
        modbot = pathlib.Path.cwd() / "modbot"
        cogs = modbot / "cogs"

        for path in cogs.iterdir():
            if path.stem.startswith("_") or path.suffix != ".py":
                continue

            self.load_extension(f"modbot.cogs.{path.stem}")

    def get_context(self, message: revolt.Message):
        return Context

    async def on_ready(self):
        logging.info("Ready")
        logging.info("Logged into %s", self.user.name)

    async def on_raw_reaction_add(self, channel_id: str, message_id: str, user_id: str, emoji: str):
        if not self.reaction_role_messages.get(message_id):
            return  # we store this as a lru dict to avoid querying the same message multiple times in a short span
                    # ie someone pings everyone and the message is getting loads of reactions

        async with self.database.acquire() as conn:
            is_menu = self.reaction_role_messages[message_id] = await conn.fetchval("select exists(*) from reaction_role_messages where id=$1", message_id)

            if is_menu:
                role_id = await conn.fetchval("select role_id from reaction_roles where message_id=$1 and emoji=$2", message_id, emoji)

                channel = self.get_channel(channel_id)
                assert isinstance(channel, revolt.TextChannel)

                member = channel.server.get_member(user_id)

                new_roles = member.roles.copy()
                new_roles.append(role_id)

                await member.edit(roles=new_roles)

    async def on_raw_reaction_remove(self, channel_id: str, message_id: str, user_id: str, emoji: str):
        if not self.reaction_role_messages.get(message_id):
            return

        async with self.database.acquire() as conn:
            is_menu = self.reaction_role_messages[message_id] = await conn.fetchval("select exists(*) from reaction_role_messages where id=$1", message_id)

            if is_menu:
                role_id = await conn.fetchval("select role_id from reaction_roles where message_id=$1 and emoji=$2", message_id, emoji)

                channel = self.get_channel(channel_id)
                assert isinstance(channel, revolt.TextChannel)

                member = channel.server.get_member(user_id)

                new_roles = member.roles.copy()

                try:
                    new_roles.remove(role_id)
                except ValueError:
                    return
                else:
                    await member.edit(roles=new_roles)

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
