from contextlib import suppress
from datetime import timedelta

import dateparser
import discord
from discord.ext.commands import ChannelNotFound, TextChannelConverter

from core import Context
from models import Scrim
from utils import emote, string_input

__all__ = ("MatchTimeEditor",)


class MatchTimeEditor(discord.ui.Button):
    def __init__(self, ctx: Context):
        self.ctx = ctx

        super().__init__(label="Set Match Time", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _e = discord.Embed(color=0x00FFB3)
        _e.description = (
            "Please enter the time of matches/scrims in the following format:\n"
            "`#registration_channel match_time`\n\n"
            "Note that slotmanager will automatically lock for the scrim at specified time. This means "
            "that `users will not be able to cancel/claim after the specified time.`\n\n"
            "**Separate multiple match time with a new line.**"
        )
        _e.set_image(url="https://cdn.discordapp.com/attachments/851846932593770496/931035634464849970/unknown.png")
        _e.set_footer(text="You only have to enter match time once, I'll handle the rest automatically.")
        await interaction.followup.send(embed=_e, ephemeral=True)
        match_times = await string_input(
            self.ctx,
            lambda x: x.author == interaction.user and x.channel == self.ctx.channel,
            delete_after=True,
            timeout=300,
        )

        match_times = match_times.strip().split("\n")
        for _ in match_times:
            with suppress(AttributeError, ValueError, ChannelNotFound, TypeError):
                channel, time = _.strip().split()
                if not all((channel, time)):
                    continue

                _c = await TextChannelConverter().convert(self.ctx, channel.strip())
                parsed = dateparser.parse(
                    time,
                    settings={
                        # "RELATIVE_BASE": self.ctx.bot.current_time,
                        "TIMEZONE": "Asia/Kolkata",
                        "RETURN_AS_TIMEZONE_AWARE": True,
                    },
                )

                parsed = parsed + timedelta(hours=24) if parsed < self.ctx.bot.current_time else parsed

                if not all((_c, parsed, parsed > self.ctx.bot.current_time)):
                    continue

                scrim = await Scrim.get_or_none(guild_id=self.ctx.guild.id, registration_channel_id=_c.id)
                if scrim:
                    await self.ctx.bot.reminders.create_timer(parsed, "scrim_match", scrim_id=scrim.id)
                    await Scrim.filter(pk=scrim.pk).update(match_time=parsed)

        await interaction.followup.send(f"{emote.check} Done, click Match-Time button to see changes.", ephemeral=True)
