from models import Guild, Tourney, Scrim, Autorole
from core import Cog, Quotient
import discord, config


class MainEvents(Cog, name="Main Events"):
    def __init__(self, bot: Quotient):
        self.bot = bot

    # incomplete, I know
    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await Guild.create(guild_id=guild.id)
        self.bot.guild_data[guild.id] = {"prefix": "q", "color": self.bot.color, "footer": config.FOOTER}
        await guild.chunk()

    @Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await Guild.filter(guild_id=guild.id).delete()
        await Scrim.filter(guild_id=guild.id).delete()
        await Tourney.filter(guild_id=guild.id).delete()
        await Autorole.filter(guild_id=guild.id).delete()
        self.bot.guild_data.pop(guild.id)
