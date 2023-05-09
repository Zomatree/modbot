from revolt.ext import commands

__all__ = ("server_only",)

def server_only():
    def inner(ctx: commands.Context):
        if not ctx.channel.server_id:
            raise commands.ServerOnly

        return True

    return commands.check(inner)
