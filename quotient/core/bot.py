import logging
import os

import discord
from discord.ext import commands

__all__ = ("Quotient",)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class Quotient(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix="q",
            enable_debug_events=True,
            intents=intents,
        )

    async def start(self) -> None:
        await super().start(os.getenv("DISCORD_TOKEN"), reconnect=True)
