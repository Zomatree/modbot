import datetime

import revolt
from revolt.ext import commands

from ..client import Client, Context
from ..utils import ModAction, TimedeltaConverter, generate_id, server_only

mod_actions = {
    ModAction.ban: ("#ff0000", "banned"),
    ModAction.kick: ("#ffff00", "kicked"),
    ModAction.timeout: ("#550055", "timed out"),
    ModAction.warn: ("#0000ff", "warned"),
}


class Moderation(commands.Cog[Client]):
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(
        self,
        ctx: Context,
        member: commands.MemberConverter | str,
        *,
        reason: str | None,
    ):
        if isinstance(member, str):
            await ctx.client.http.ban_member(ctx.server.id, member, reason)
            member_id = member
            avatar_url = None
            member_name = None
        else:
            await member.ban(reason=reason)
            member_id = member.id
            avatar_url = member.avatar.url if member.avatar else None
            member_name = member.name

        action_id = generate_id()

        async with ctx.client.database.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "insert into mod_actions(id, server_id, moderator_id, action, user_id, reason) values ($1, $2, $3, $4, $5, $6)",
                    action_id,
                    ctx.server.id,
                    ctx.author.id,
                    ModAction.ban,
                    member_id,
                    reason,
                )

                res = await conn.execute(
                    "select id from mod_actions where server_id=$1 and user_id=$2",
                    ctx.server.id,
                    member_id,
                )
                num = res.split(" ")[0]

        colour, action_text = mod_actions[ModAction.ban]

        description = (
            f"{ctx.author.mention} ({ctx.author.name}) {action_text} <@{member_id}> {f'({member_name})' if member_name else ''}\n"
            f"Reason: `{reason or 'none'}`\n"
            f"Warn ID: `{id}`\n"
            f"This is ban number {num} for this user."
        )

        embed = revolt.SendableEmbed(
            title=f"User {action_text}",
            colour=colour,
            description=description,
        )

        if avatar_url:
            embed.icon_url = avatar_url

        await ctx.send(embed=embed)

        if log_channel_id := await ctx.client.get_server_log_channel(ctx.server.id):
            log_channel = ctx.client.get_channel(log_channel_id)
            assert isinstance(log_channel, revolt.TextChannel)

            await log_channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(
        self, ctx: Context, member: commands.MemberConverter, *, reason: str | None
    ):
        await member.kick()

        action_id = generate_id()

        async with ctx.client.database.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "insert into mod_actions(id, server_id, moderator_id, action, user_id, reason) values ($1, $2, $3, $4, $5, $6)",
                    action_id,
                    ctx.server.id,
                    ctx.author.id,
                    ModAction.kick,
                    member.id,
                    reason,
                )

                res = await conn.execute(
                    "select id from mod_actions where server_id=$1 and user_id=$2",
                    ctx.server.id,
                    member.id,
                )
                num = res.split(" ")[0]

        colour, action_text = mod_actions[ModAction.kick]

        description = (
            f"{ctx.author.mention} ({ctx.author.name}) {action_text} {member.mention} ({member.name})\n"
            f"Reason: `{reason or 'none'}`\n"
            f"Warn ID: `{id}`\n"
            f"This is kick number {num} for this user."
        )

        embed = revolt.SendableEmbed(
            title=f"User {action_text}",
            colour=colour,
            description=description,
        )

        if member.avatar:
            embed.icon_url = member.avatar.url

        await ctx.send(embed=embed)

        if log_channel_id := await ctx.client.get_server_log_channel(ctx.server.id):
            log_channel = ctx.client.get_channel(log_channel_id)
            assert isinstance(log_channel, revolt.TextChannel)

            await log_channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(
        self, ctx: Context, member: commands.MemberConverter, *, reason: str | None
    ):
        action_id = generate_id()

        async with ctx.client.database.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "insert into mod_actions(id, server_id, moderator_id, action, user_id, reason) values ($1, $2, $3, $4, $5, $6)",
                    action_id,
                    ctx.server.id,
                    ctx.author.id,
                    ModAction.warn,
                    member.id,
                    reason,
                )

                res = await conn.execute(
                    "select id from mod_actions where server_id=$1 and user_id=$2",
                    ctx.server.id,
                    member.id,
                )
                num = res.split(" ")[0]

        colour, action_text = mod_actions[ModAction.warn]

        description = (
            f"{ctx.author.mention} ({ctx.author.name}) {action_text} {member.mention} ({member.name})\n"
            f"Reason: `{reason or 'none'}`\n"
            f"Warn ID: `{id}`\n"
            f"This is warn number {num} for this user."
        )

        embed = revolt.SendableEmbed(
            title=f"User {action_text}",
            colour=colour,
            description=description,
        )

        if member.avatar:
            embed.icon_url = member.avatar.url

        await ctx.send(embed=embed)

        if log_channel_id := await ctx.client.get_server_log_channel(ctx.server.id):
            log_channel = ctx.client.get_channel(log_channel_id)
            assert isinstance(log_channel, revolt.TextChannel)

            await log_channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def timeout(
        self,
        ctx: Context,
        member: commands.MemberConverter,
        *,
        length: TimedeltaConverter,
    ):
        if member.current_timeout:
            return await ctx.embed_send(
                "This user is already timed out.", status="fail"
            )

        await member.timeout(length)

        action_id = generate_id()

        async with ctx.client.database.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "insert into mod_actions(id, server_id, moderator_id, action, user_id, reason) values ($1, $2, $3, $4, $5, $6)",
                    action_id,
                    ctx.server.id,
                    ctx.author.id,
                    ModAction.timeout,
                    member.id,
                    None,
                )

                res = await conn.execute(
                    "select id from mod_actions where server_id=$1 and user_id=$2",
                    ctx.server.id,
                    member.id,
                )
                num = res.split(" ")[0]

        colour, action_text = mod_actions[ModAction.timeout]

        finishes_at = (datetime.datetime.utcnow() + length).timestamp()

        description = (
            f"{ctx.author.mention} ({ctx.author.name}) {action_text} {member.mention} ({member.name})\n"
            f"Timeout expires: <t:{finishes_at}>"
            f"Warn ID: `{id}`\n"
            f"This is timeout number {num} for this user."
        )

        embed = revolt.SendableEmbed(
            title=f"User {action_text}",
            colour=colour,
            description=description,
        )

        if member.avatar:
            embed.icon_url = member.avatar.url

        await ctx.send(embed=embed)

        if log_channel_id := await ctx.client.get_server_log_channel(ctx.server.id):
            log_channel = ctx.client.get_channel(log_channel_id)
            assert isinstance(log_channel, revolt.TextChannel)

            await log_channel.send(embed=embed)


def setup(client: Client):
    client.add_cog(Moderation())


def teardown(client: Client):
    client.remove_cog("Moderation")
