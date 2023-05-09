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

time_regex = re.compile(r"(\d{1,5}(?:[.,]?\d{1,5})?)([smhd])")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


class TimedeltaConverterError(commands.ConverterError):
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

def message_converter(ctx: Context, argument: str) -> revolt.Message:
    ...

def role_converter(ctx: Context, argument: str) -> revolt.Role:
    ...

TimedeltaConverter = Annotated[datetime.timedelta, timedelta_converter]
MessageConverter = Annotated[revolt.Message, message_converter]
RoleConverter = Annotated[revolt.Role, role_converter]
