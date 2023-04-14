import revolt
from revolt.ext import commands

from ..client import Client, Context
from ..utils import server_only


class Config(commands.Cog[Client]):
    @commands.group()
    @server_only()
    @commands.has_permissions(manage_server=True)
    async def prefix(self, ctx: Context) -> None:
        prefixes = "\n".join(
            f"- {prefix} "
            for prefix in await ctx.client.get_server_prefix(ctx.server.id)
        )

        await ctx.embed_send(f"The prefix(s) here are: {prefixes}", status="ok")

    @prefix.command(name="set")
    @server_only()
    @commands.has_permissions(manage_server=True)
    async def prefix_set(self, ctx: Context, prefix: str):
        if len(prefix) > 8:
            return await ctx.embed_send("The prefix is too long.", status="fail")

        async with ctx.client.database.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "insert into server_configs (server_id, prefix) values ($1, $2) on conflict (server_id) do update set prefix=$2",
                    ctx.server.id,
                    prefix,
                )

        ctx.client.prefixes[ctx.server.id] = prefix

        await ctx.embed_send(
            f"Sucessfully set the server's prefix to {prefix}", status="ok"
        )

    @commands.group()
    @server_only()
    @commands.has_permissions(manage_server=True)
    async def logs(self, ctx: Context) -> None:
        log_channel_id = await ctx.client.get_server_log_channel(ctx.server.id)

        await ctx.embed_send(
            f"The log channel for this server is <#{log_channel_id}>", status="ok"
        )

    @logs.command(name="set")
    @server_only()
    @commands.has_permissions(manage_server=True)
    async def logs_set(self, ctx: Context, channel: commands.ChannelConverter):
        if not isinstance(channel, revolt.TextChannel):
            return await ctx.embed_send(
                "That channel is not a text channel.", status="fail"
            )

        async with ctx.client.database.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "insert into server_configs (server_id, log_channel) values ($1, $2) on conflict (server_id) do update set log_channel=$2",
                    ctx.server.id,
                    channel.id,
                )

        ctx.client.log_channels[ctx.server.id] = channel.id

        await ctx.embed_send(
            f"Sucessfully set the server's log channel to {channel.mention}",
            status="ok",
        )


def setup(client: Client):
    client.add_cog(Config())


def teardown(client: Client):
    client.remove_cog("Config")
