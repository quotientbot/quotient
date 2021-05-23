from models import Autorole, ArrayRemove
from core import Cog, Quotient
import discord


class CmdEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener(name="on_member_join")
    async def on_autorole(self, member: discord.Member):
        guild = member.guild

        record = await Autorole.get_or_none(guild_id=guild.id)
        if not record:
            return

        elif not member.bot and len(record.humans):
            for role in record.humans:
                try:
                    await member.add_roles(discord.Object(id=role), reason="Quotient's autorole")
                except discord.Forbidden:
                    await Autorole.filter(guild_id=guild.id).update(humans=ArrayRemove("humans", role))
                    continue

        elif member.bot and len(record.bots):
            for role in record.bots:
                try:
                    await member.add_roles(discord.Object(id=role), reason="Quotient's autorole")
                except discord.Forbidden:
                    await Autorole.filter(guild_id=guild.id).update(bots=ArrayRemove("bots", role))
                    continue
        else:
            return
