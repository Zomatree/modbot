import datetime
import re
from typing import Annotated

from revolt.ext import commands

time_regex = re.compile(r"(\d{1,5}(?:[.,]?\d{1,5})?)([smhd])")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


class TimedeltaConverterError(commands.ConverterError):
    pass


def timedelta_converter(ctx: commands.Context, argument: str) -> datetime.timedelta:
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


TimedeltaConverter = Annotated[datetime.timedelta, timedelta_converter]
