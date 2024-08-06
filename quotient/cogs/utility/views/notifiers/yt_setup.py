from datetime import timedelta

import discord
from cogs.premium import Feature, can_use_feature, prompt_premium_plan
from core import QuoView
from discord.ext import commands
from lib import (
    DIAMOND,
    YOUTUBE,
    guild_role_input,
    text_channel_input,
    text_input_modal,
    truncate_string,
)

from quotient.models import Guild, YtNotification


class SetChannel(discord.ui.Button):
    view: "SetupNewYt"

    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Discord Channel")

    async def callback(self, inter: discord.Interaction):
        await inter.response.defer(ephemeral=True, thinking=True)
        ch = await text_channel_input(inter, "Select the channel to send YT Notifications.")
        if not ch:
            return

        if not ch.permissions_for(inter.guild.me).embed_links:
            return await inter.followup.send(f"I need the `Embed Links` permission in {ch.mention}.", ephemeral=True)

        self.view.record.discord_channel_id = ch.id
        await self.view.update_msg()


class YtUsername(discord.ui.Button):
    view: "SetupNewYt"

    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="YT Username (@)")

    async def callback(self, inter: discord.Interaction):
        yt_user_name = await text_input_modal(inter, "Youtube Channel Form", "Enter YT Channel Username")
        if not yt_user_name:
            return

        yt_channel = await self.view.record.search_yt_channel(yt_user_name)
        if not yt_channel:
            return await inter.followup.send(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    title="Invalid Youtube Handle",
                    description=(
                        "You have entered an invalid Youtube Handle, Please try again.\n\n"
                        "If you are facing trouble, please visit [Youtube Docs](https://support.google.com/youtube/answer/6180214?hl=en)"
                    ),
                ),
                view=self.view.bot.contact_support_view(),
            )

        prompt = await self.view.bot.prompt(
            inter,
            inter.user,
            f"Is this the correct channel?\n> {yt_channel.snippet.title}\n> {truncate_string(yt_channel.snippet.description, 100)}\n> [**Channel Link**]({yt_channel.yt_channel_url})",
            thumbnail=yt_channel.snippet.thumbnail,
        )

        if not prompt:
            return await inter.followup.send(
                "Oh! Ok, Please try again with a valid channel handle.", view=self.view.bot.contact_support_view(), ephemeral=True
            )

        self.view.bot.logger.debug(f"YT Channel Username: {yt_user_name}, YT Channel ID: {yt_channel.id}")
        self.view.record.yt_channel_id = yt_channel.id
        self.view.record.yt_channel_username = yt_user_name
        await self.view.update_msg()


class SetRegularVideoMsg(discord.ui.Button):
    view: "SetupNewYt"

    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Regular Video Message")

    async def callback(self, inter: discord.Interaction):
        msg = await text_input_modal(
            inter,
            "Regular Video Message",
            "Enter the message:",
            placeholder=self.view.record.regular_video_msg,
            default=self.view.record.regular_video_msg,
            max_length=255,
            min_length=6,
            input_type="long",
        )
        if not msg:
            return

        self.view.record.regular_video_msg = msg
        await self.view.update_msg()


class SetLiveVideoMsg(discord.ui.Button):
    view: "SetupNewYt"

    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Live Video Message")

    async def callback(self, inter: discord.Interaction):
        is_allowed, min_tier = await can_use_feature(Feature.YT_LIVE_NOTI_SETUP, inter.guild_id)
        if not is_allowed:
            return await prompt_premium_plan(
                inter, text=f"You server needs to be on **{min_tier.name}** tier to setup 'Youtube Live Video Notifications'."
            )

        msg = await text_input_modal(
            inter,
            "Live Video Message",
            "Enter the message:",
            placeholder=self.view.record.live_video_msg,
            default=self.view.record.live_video_msg,
            max_length=255,
            min_length=6,
            input_type="long",
        )
        if not msg:
            return

        self.view.record.live_video_msg = msg
        await self.view.update_msg()


class SetPingRole(discord.ui.Button):
    view: "SetupNewYt"

    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Ping Role")

    async def callback(self, inter: discord.Interaction):
        await inter.response.defer(ephemeral=True, thinking=True)
        role = await guild_role_input(
            inter, "Select the role to ping for notifications.\n\nThis will replace `{ping}` in the message."
        )
        if not role:
            return

        self.view.record.ping_role_id = role.id
        await self.view.update_msg()


class SaveDetails(discord.ui.Button):
    view: "SetupNewYt"

    def __init__(self, disabled: bool = True):
        super().__init__(style=discord.ButtonStyle.success, label="Save", disabled=disabled)

    async def callback(self, inter: discord.Interaction):
        await inter.response.defer(ephemeral=True)

        is_allowed, min_tier = await can_use_feature(Feature.YT_NOTI_SETUP, inter.guild_id)
        if not is_allowed:
            return await prompt_premium_plan(
                inter, text=f"You server needs to be on **{min_tier.name}** tier to setup more 'Youtube Notifications'."
            )

        await self.view.record.setup()

        self.view.stop()
        from .yt_main import YtNotificationView

        v = YtNotificationView(self.view.ctx)
        v.message = await self.view.message.edit(embed=await v.initial_msg(), view=v)


class CancelSetup(discord.ui.Button):
    view: "SetupNewYt"

    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="Cancel")

    async def callback(self, inter: discord.Interaction):
        await inter.response.defer(ephemeral=True)

        prompt = await self.view.bot.prompt(inter, inter.user, "Are you sure you want to cancel the setup?")
        if not prompt:
            return

        self.view.stop()
        from .yt_main import YtNotificationView

        v = YtNotificationView(self.view.ctx)
        v.message = await self.view.message.edit(embed=await v.initial_msg(), view=v)


class SetupNewYt(QuoView):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, timeout=100)

        self.record: YtNotification = None

    async def initial_msg(self) -> discord.Embed:
        if not self.record:
            self.record = YtNotification(discord_guild_id=self.ctx.guild.id)

        g = await Guild.get_or_none(guild_id=self.ctx.guild.id)

        self.clear_items()
        self.add_item(SetChannel())
        self.add_item(YtUsername())
        self.add_item(SetRegularVideoMsg())
        self.add_item(SetLiveVideoMsg())
        self.add_item(SetPingRole())
        self.add_item(
            SaveDetails(
                disabled=not all(
                    [
                        self.record.discord_channel_id,
                        self.record.yt_channel_id,
                        self.record.regular_video_msg,
                        self.record.live_video_msg,
                    ]
                )
            )
        )
        self.add_item(CancelSetup())

        e = discord.Embed(
            color=self.bot.color,
            title="Setup New Youtube Notification",
            url=self.bot.config("SUPPORT_SERVER_LINK"),
        )

        e.add_field(
            name="Discord Channel",
            value=f"<#{self.record.discord_channel_id}>" if self.record.discord_channel_id else "`Not Set`",
            inline=False,
        )
        e.add_field(
            name="YT Handle",
            value=(
                f"[{YOUTUBE} {self.record.yt_channel_username}]({self.record.yt_channel_url})"
                if self.record.yt_channel_username
                else "`Not Set`"
            ),
            inline=False,
        )
        e.add_field(
            name="Ping Role",
            value=f"<@&{self.record.ping_role_id}>" if self.record.ping_role_id else "`Not Set`",
            inline=False,
        )

        e.add_field(
            name="Regular Video Message",
            value=self.record.regular_video_msg,
            inline=False,
        )
        e.add_field(
            name=f"{DIAMOND} Live Video Message (Premium Only)",
            value=self.record.live_video_msg,
            inline=False,
        )

        return e

    async def update_msg(self):
        await self.message.edit(embed=await self.initial_msg(), view=self)
