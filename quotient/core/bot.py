import logging

import discord
from discord.ext import commands

__all__ = ("Quotient",)


class Quotient(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix="q",
            enable_debug_events=True,
            intents=discord.Intents.all(),
        )

    async def start(self) -> None:
        print("Bot is ready.")
        logging.info("Bot is ready.")

        log = logging.getLogger()
        log.info(f"Bot is ready. {self.user}")

        await super().start("", reconnect=True)
