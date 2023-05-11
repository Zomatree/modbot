from __future__ import annotations

import datetime
import re
from typing import TYPE_CHECKING, Annotated
import revolt

from revolt.ext import commands

if TYPE_CHECKING:
    from ..client import Context

__all__ = (
    "time_regex",
    "time_dict",
    "TimedeltaConverterError",
    "timedelta_converter",
    "TimedeltaConverter",
    "message_converter",
    "MessageConverter",
    "MissingRequiredArgument",
    "RoleConverter"
)

id_regex = re.compile(r"[0-9A-HJKMNP-TV-Z]{26}")
time_regex = re.compile(r"(\d{1,5}(?:[.,]?\d{1,5})?)([smhd])")
message_link_regex = re.compile(r"(?:http(?:s)?:\/\/)?(?:\w+\.?)+?\/server\/(?P<server>[0-9A-HJKMNP-TV-Z]{26})\/channel\/(?P<channel>[0-9A-HJKMNP-TV-Z]{26})\/(?P<message>[0-9A-HJKMNP-TV-Z]{26})")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}

class TimedeltaConverterError(commands.ConverterError):
    pass

class MessageConverterError(commands.ConverterError):
    pass

class RoleConverterError(commands.ConverterError):
    pass

class MissingRequiredArgument(commands.CommandError):
    pass

def timedelta_converter(ctx: Context, argument: str) -> datetime.timedelta:
    matches = time_regex.findall(argument.lower())
    time = 0

    for v, k in matches:
        try:
            time += time_dict[k] * float(v)

        except KeyError:
            raise TimedeltaConverterError(
                f"{k} is an invalid time-key! h/m/s/d are valid!"
            )

        except ValueError:
            raise TimedeltaConverterError(f"{v} is not a number!")

    return datetime.timedelta(seconds=time)

async def message_converter(ctx: Context, argument: str) -> revolt.Message:
    if match := message_link_regex.match(argument):
        try:
            server = ctx.client.get_server(match.group("server"))
            channel = server.get_channel(match.group("channel"))
            if not isinstance(channel, revolt.Messageable):
                raise MessageConverterError

            message = await channel.fetch_message(match.group("message"))
        except (LookupError, revolt.HTTPError):
            raise MessageConverterError

    elif match := id_regex.match(argument):
        try:
            message = await ctx.channel.fetch_message(argument)
        except revolt.HTTPError:
            raise MessageConverterError

    else:
        for message in ctx.client.state.messages:
            if message.id == argument:
                break
        else:
            raise MessageConverterError

    return message


def role_converter(ctx: Context, argument: str) -> revolt.Role:
    if role := ctx.server.get_role(argument):
        return role

    for role in ctx.server.roles:
        if role.name == argument:
            return role

    raise RoleConverterError

TimedeltaConverter = Annotated[datetime.timedelta, timedelta_converter]
MessageConverter = Annotated[revolt.Message, message_converter]
RoleConverter = Annotated[revolt.Role, role_converter]
