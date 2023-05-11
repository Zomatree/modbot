import asyncpg
from revolt.ext import commands

from ..client import Client, Context
from ..utils import server_only, MessageConverter, MissingRequiredArgument, RoleConverter

class ReactionRoles(commands.Cog[Client]):
    @commands.group(aliases=["rroles", "roles", "r_roles"])
    @server_only()
    @commands.has_permissions(manage_roles=True)
    async def reaction_roles(self, ctx: Context):
        await ctx.send_help(self.reaction_roles)

    @reaction_roles.command()
    @server_only()
    @commands.has_permissions(manage_roles=True)
    async def create(self, ctx: Context, message: MessageConverter | None = None):
        if not message and ctx.message.replies:
            message = ctx.message.replies[0]
        else:
            raise MissingRequiredArgument("message")

        async with ctx.client.database.acquire() as conn:
            async with conn.transaction():
                try:
                    await conn.execute("insert into reaction_role_messages(id, server_id) values ($1, $2)", message.id, ctx.server.id)
                except asyncpg.UniqueViolationError:
                    return await ctx.embed_send("This message is already setup to be a reaction role menu", status="fail")

        await ctx.embed_send(f"Message has been turned into a reaction role menu, run `{await ctx.client.get_server_prefix(ctx.server.id)}reaction_roles create` to add roles.")

    @reaction_roles.command()
    @server_only()
    @commands.has_permissions(manage_roles=True)
    async def delete(self, ctx: Context, message: MessageConverter | None = None):
        if not message and ctx.message.replies:
            message = ctx.message.replies[0]
        else:
            raise MissingRequiredArgument("message")

        async with ctx.client.database.acquire() as conn:
            async with conn.transaction():
                status = await conn.execute("delete from reaction_role_messages where id=$1", message.id)

                if status == "DELETE 1":
                    await ctx.embed_send("Message is no longer a reaction role menu.")

                    await message.remove_all_reactions()
                else:
                    await ctx.embed_send("That message is not a reaction role menu", status="fail")

    @reaction_roles.command()
    @server_only()
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx: Context, message: MessageConverter | None, role: RoleConverter, emoji: str):
        if not message and ctx.message.replies:
            message = ctx.message.replies[0]
        else:
            raise MissingRequiredArgument("message")

        try:
            await message.add_reaction(emoji)
        except:
            return await ctx.embed_send("Invalid emoji", status="fail")

        async with ctx.client.database.acquire() as conn:
            async with conn.transaction():
                try:
                    await conn.execute("insert into reaction_roles values ($1, $2, $3)", message.id, role.id, emoji)
                except asyncpg.ForeignKeyViolationError:
                    await message.remove_reaction(emoji)
                    return await ctx.embed_send("That message is not an existing reaction role menu", status="fail")

    @reaction_roles.command()
    @server_only()
    @commands.has_permissions(manage_roles=True)
    async def remove(self, ctx: Context, message: MessageConverter | None, argument: RoleConverter | str, emoji: str):
        if not message and ctx.message.replies:
            message = ctx.message.replies[0]
        else:
            raise MissingRequiredArgument("message")

        async with ctx.client.database.acquire() as conn:
            async with conn.transaction():
                status = await conn.execute("delete from reaction_roles where message_id=$1 and emoji=$2", message.id, emoji)

        if status == "DELETE 1":
            await message.remove_reaction(emoji)
            return await ctx.embed_send("no role with that emoji found on that message.", status="fail")

def setup(client: Client):
    client.add_cog(ReactionRoles())


def teardown(client: Client):
    client.remove_cog("ReactionRoles")
