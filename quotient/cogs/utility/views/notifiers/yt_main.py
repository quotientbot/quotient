import discord
from cogs.premium import Feature, can_use_feature, prompt_premium_plan
from core import QuoView
from discord.ext import commands
from lib import INFO, YOUTUBE

from quotient.models import YtNotification

from .yt_setup import SetupNewYt


class YTNotifierSelector(discord.ui.Select):
    view: discord.ui.View

    def __init__(self, records: list[YtNotification]):
        options = [
            discord.SelectOption(
                label=f"{record.yt_channel_username}",
                value=str(record.id),
                emoji=YOUTUBE,
            )
            for record in records
        ]
        super().__init__(placeholder="Select a Youtube Channel", options=options)

    async def callback(self, inter: discord.Interaction):
        await inter.response.defer()

        self.view.record_id = self.values[0]
        self.view.stop()


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

        is_allowed, min_tier = await can_use_feature(Feature.YT_NOTI_SETUP, inter.guild_id)
        if not is_allowed:
            return await prompt_premium_plan(
                inter, text=f"You server needs to be on **{min_tier.name}** tier to setup more 'Youtube Notifications'."
            )

        self.stop()
        v = SetupNewYt(self.ctx)
        v.message = await self.message.edit(embed=await v.initial_msg(), view=v)

    @discord.ui.button(label="Delete Setup", style=discord.ButtonStyle.danger)
    async def del_yt_noti(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        records = await YtNotification.filter(discord_guild_id=inter.guild_id)
        if not records:
            return

        v = discord.ui.View()
        v.add_item(YTNotifierSelector(records))
        v.message = await inter.followup.send("Which channel don't you want to get notifications from?", view=v, ephemeral=True)

        await v.wait()
        if not getattr(v, "record_id", None):
            return

        r = await YtNotification.get(id=v.record_id)
        await r.delete()

        await v.message.edit(content="", embed=self.bot.success_embed("Deleted successfully!"), view=None)

        view = YtNotificationView(self.ctx)
        view.message = await self.message.edit(embed=await view.initial_msg(), view=view)
