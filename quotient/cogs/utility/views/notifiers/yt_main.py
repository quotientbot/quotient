import discord
from cogs.premium import YT_NOTIFICATIONS_LIMIT, RequirePremiumView
from core import QuoView
from discord.ext import commands
from lib import INFO, YOUTUBE
from models import YtNotification

from .yt_setup import SetupNewYt


class YtNotificationView(QuoView):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, timeout=100)

    async def initial_msg(self) -> discord.Embed:
        records = await YtNotification.filter(discord_guild_id=self.ctx.guild.id)

        self.add_item(
            discord.ui.Button(
                label="Contact Support",
                style=discord.ButtonStyle.link,
                url=self.bot.config("SUPPORT_SERVER_LINK"),
                emoji=INFO,
            )
        )

        e = discord.Embed(
            color=self.bot.color,
            title="Quotient - Youtube Notifications",
            description="",
            url=self.bot.config("SUPPORT_SERVER_LINK"),
        )

        for idx, record in enumerate(records, start=1):
            e.description += (
                f"`{idx}.` <#{record.discord_channel_id}> - [{YOUTUBE}@{record.yt_channel_username}]({record.yt_channel_url})\n"
            )

        if not records:
            e.description = "```Click 'Setup New' to setup YT notifications```"
            self.children[1].disabled = True

        return e

    @discord.ui.button(label="Setup New", style=discord.ButtonStyle.primary)
    async def setup_new_yt(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()
        if not await self.bot.is_pro_guild(inter.guild_id):
            if await YtNotification.filter(discord_guild_id=inter.guild_id).count() >= YT_NOTIFICATIONS_LIMIT:
                v = RequirePremiumView(f"You can setup only {YT_NOTIFICATIONS_LIMIT} Youtube Notification in free version.")
                v.message = await inter.followup.send(embed=v.premium_embed, view=v)
                return

        self.stop()
        v = SetupNewYt(self.ctx)
        v.message = await self.message.edit(embed=await v.initial_msg(), view=v)

    @discord.ui.button(label="Delete Setup", style=discord.ButtonStyle.danger)
    async def del_yt_noti(self, inter: discord.Interaction, btn: discord.ui.Button): ...
