from textwrap import indent

import revolt
from typing import cast
from revolt.ext import commands

from ..client import Client, Context

prefix = "\u200b \u200b \u200b "

class HelpCommand(commands.HelpCommand[Client]):
    async def create_bot_help(
        self,
        context: commands.Context,
        commands: dict[commands.Cog[Client] | None, list[commands.Command[Client]]],
    ) -> str:
        lines: list[str] = []

        for cog, cog_commands in commands.items():
            cog_lines: list[str] = []
            cog_lines.append(f"{cog.qualified_name if cog else 'No Category'}:")

            for command in cog_commands:
                cog_lines.append(
                    f"{prefix}{command.name} - {command.short_description or 'No description'}"
                )

            cog_lines.append("")

            lines.append("\n".join(cog_lines))

        return "\n".join(lines).rstrip()

    async def create_cog_help(self, context: commands.Context, cog: commands.Cog[Client]) -> str:
        lines: list[str] = []

        lines.append(f"{cog.qualified_name}:")

        for command in cog.commands:
            lines.append(
                f"{prefix}{command.name} - {command.short_description or 'No description'}"
            )

        return "\n".join(lines)

    async def create_command_help(
        self, context: commands.Context, command: commands.Command[Client]
    ) -> str:
        lines: list[str] = []

        lines.append(f"{command.name}:")
        lines.append(f"{prefix}Usage: {command.get_usage()}")

        if command.aliases:
            lines.append(f"{prefix}Aliases: {', '.join(command.aliases)}")

        if command.description:
            lines.append(indent(command.description, "{prefix}"))

        return "\n".join(lines)

    async def create_group_help(
        self, context: commands.Context, group: commands.Group[Client]
    ) -> str:
        lines: list[str] = []

        lines.append(f"{group.name}:")
        lines.append(f"{prefix}Usage: {group.get_usage()}")

        if group.aliases:
            lines.append(f"{prefix}Aliases: {', '.join(group.aliases)}")

        if group.description:
            lines.append(indent(group.description, "\u200b \u200b \u200b"))

        for command in group.commands:
            lines.append(
                f"{prefix}{command.name} - {command.short_description or 'No description'}"
            )

        return "\n".join(lines)

    async def send_help_command(
        self, context: commands.Context, message_payload: commands.MessagePayload
    ) -> revolt.Message:
        context = cast(Context, context)
        return await context.embed_send(message_payload["content"])

    async def handle_no_cog_found(self, context: commands.Context, name: str):
        context = cast(Context, context)
        return await context.embed_send(
            f"No category called `{name}` found.", status="fail"
        )

    async def handle_no_command_found(self, context: commands.Context, name: str):
        context = cast(Context, context)
        return await context.embed_send(f"No command called `{name}` found.", status="fail")


def setup(client: Client):
    client.help_command = HelpCommand()

def teardown(client: Client):
    client.help_command = commands.DefaultHelpCommand[Client]()
