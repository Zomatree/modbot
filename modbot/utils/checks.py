from revolt.ext import commands


def server_only():
    def inner(ctx: commands.Context):
        if not ctx.channel.server_id:
            raise commands.ServerOnly

        return True

    return commands.check(inner)
