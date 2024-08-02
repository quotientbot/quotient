import asyncio
import json
from typing import Literal

import discord
from discord.ext import commands


class BlacklistManager:
    def __init__(self):
        self.lock = asyncio.Lock()
        self._db: dict[int, dict] = {}
        self.file_path = "quotient/blacklist.json"

        self.load_file()

    def load_file(self):
        try:
            with open(self.file_path, "r") as f:
                self._db = json.load(f)
        except FileNotFoundError:
            print(f"{self.file_path} not found.")
            self._db = {}  # Initialize empty if not found
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {self.file_path}.")
            self._db = {}  # Initialize empty on JSON error

    async def save(self):
        try:
            with open(self.file_path, "w") as f:
                json.dump(self._db, f, indent=4)
        except Exception as e:
            print(f"Error saving to {self.file_path}: {e}")

    async def put(self, obj_id: str, reason: str, _type: Literal["user", "guild"], blocked_at: str, blocked_by: str):
        self.load_file()  # Ensure the latest data is loaded
        async with self.lock:
            self._db[obj_id] = {"reason": reason, "type": _type, "at": blocked_at, "by": blocked_by}
            await self.save()

    async def remove(self, obj_id: str):
        self.load_file()

        try:
            del self._db[obj_id]
        except KeyError:
            return False

        await self.save()

    async def is_blacklisted(self, obj_id: str):
        self.load_file()
        return obj_id in self._db

    def all_blacklisted(self):
        self.load_file()
        return self._db

    async def log_spammer(
        self,
        bot: commands.AutoShardedBot,
        message: discord.Message,
        retry_after: float,
        *,
        autoblock: bool = False,
    ):
        guild_name = getattr(message.guild, "name", "No Guild Name")
        guild_id = getattr(message.guild, "id", None)
        fmt = "User %s (ID %s) in guild %r (ID %s) spamming, retry_after: %.2fs"

        bot.logger.warning(fmt, message.author, message.author.id, guild_name, guild_id, retry_after)
        if not autoblock:
            return

        try:
            await message.reply(
                embed=discord.Embed(
                    title="Spam Detected",
                    description="You have been blocked from using commands for spamming, If you believe this is a mistake, please contact staff.",
                    colour=0xDDA453,
                ),
                view=bot.contact_support_view(),
            )
        except discord.HTTPException:
            pass

        embed = discord.Embed(title="Auto-blocked Member", colour=0xDDA453)
        embed.add_field(name="Member", value=f"{message.author} (ID: {message.author.id})", inline=False)
        embed.add_field(name="Guild Info", value=f"{guild_name} (ID: {guild_id})", inline=False)
        embed.add_field(name="Channel Info", value=f"{message.channel} (ID: {message.channel.id}", inline=False)
        embed.timestamp = discord.utils.utcnow()
        return await bot.logs_webhook.send(embed=embed, username=bot.user.name, avatar_url=bot.user.default_avatar.url)
