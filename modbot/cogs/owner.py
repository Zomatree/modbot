import inspect
import re
import traceback

from revolt.ext import commands

from ..client import Client, Context

codeblock_regex = re.compile(r"```(?:\w*)\n((?:.|\n)+)\n```")


class Owner(commands.Cog[Client]):
    def __init__(self):
        self.previous_eval = None

    @commands.command()
    @commands.is_bot_owner()
    async def eval(self, ctx: Context, *, code: str):
        if match := codeblock_regex.match(code):
            code = match.group(1)

        lines = code.split("\n")
        lines[-1] = f"return {lines[-1]}"
        indented_code = "\n\t".join(lines)

        code = f"""async def _eval():\n\t{indented_code}"""

        globs = globals().copy()
        globs["ctx"] = ctx
        globs["client"] = ctx.client
        globs["server"] = ctx.server
        globs["channel"] = ctx.channel
        globs["author"] = ctx.author
        globs["message"] = ctx.message
        globs["_"] = self.previous_eval

        try:
            exec(code, globs)
            result = globs["_eval"]()

            if inspect.isasyncgen(result):
                async for value in result:
                    await ctx.send(repr(value))
                    result = None
            else:
                result = await result

                await ctx.send(str(result))

            self.previous_eval = result

        except Exception as e:
            return await ctx.send(
                f"```py\n{''.join(traceback.format_exception(type(e), e, e.__traceback__))}\n```"
            )

    @commands.command()
    @commands.is_bot_owner()
    async def reload(self, ctx: Context, *, cog: str | None = None):
        if cog is None:
            for ext in list(ctx.client.extensions):
                ctx.client.reload_extension(ext)

            await ctx.embed_send("Reloaded all cogs")

        else:
            ctx.client.reload_extension(cog)

            await ctx.embed_send(f"Reloaded `{cog}`")


def setup(client: Client):
    client.add_cog(Owner())


def teardown(client: Client):
    client.remove_cog("Owner")
