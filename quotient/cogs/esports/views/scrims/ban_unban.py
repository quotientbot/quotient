from datetime import timedelta
from typing import Any

import discord
from discord.ext import commands
from lib import (
    EXIT,
    INFO,
    TEXT_CHANNEL,
    convert_to_seconds,
    text_channel_input,
    user_input,
)

from quotient.models import ScrimsBanLog, ScrimsBannedUser

from . import ScrimsBtn, ScrimsView
from .utility.buttons import DiscardChanges


class ScrimBanManager(ScrimsView):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, timeout=100)

    async def initial_msg(self) -> discord.Embed:
        banned_users = await ScrimsBannedUser.filter(guild_id=self.ctx.guild.id).order_by("id")
        scrim_banlog = await ScrimsBanLog.get_or_none(guild_id=self.ctx.guild.id)

        self.clear_items()
        self.add_item(BanUsers(self.ctx))
        self.add_item(UnbanUsers(self.ctx, disabled=not banned_users))
        self.add_item(BannedUserInfo(self.ctx, disabled=not banned_users))

        self.add_item(SetBanlogChannel(self.ctx, row=2))
        self.add_item(DiscardChanges(self.ctx, label="Back to Main Menu", emoji=EXIT, row=2))

        embed = discord.Embed(color=self.bot.color)
        embed.description = f"**Ban / Unban users from Scrims**\n\n"

        for idx, user in enumerate(banned_users, start=1):
            embed.description += (
                f"`{idx:02}.` {getattr(user.user,'mention','Unknown User')}[`{user.user}`] - "
                f"{discord.utils.format_dt(user.banned_till,'R') if user.banned_till else '`Never`'}\n"
            )

        if not banned_users:
            embed.description += "```No users are banned.```"

        embed.description += (
            f"\n\nBan / Unban Log Channel: {getattr(scrim_banlog.channel, 'mention', 'Not Set!') if scrim_banlog else '`Not Set!`'}"
        )
        return embed

    async def refresh_view(self):
        try:
            self.message = await self.message.edit(embed=await self.initial_msg(), view=self)
        except discord.HTTPException:
            await self.on_timeout()


class BanUsers(ScrimsBtn):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, style=discord.ButtonStyle.red, label="Ban Users")

    async def callback(self, interaction: discord.Interaction):
        modal = BanFieldsInput()
        await interaction.response.send_modal(modal)

        await modal.wait()

        users_to_ban = await user_input(interaction, "Please select the users to ban ...")
        if not users_to_ban:
            return

        banned_until = convert_to_seconds(modal.ban_until.value) if modal.ban_until.value else None
        if banned_until:
            banned_until = self.view.bot.current_time + timedelta(seconds=banned_until)

        banned_count = 0

        scrim_banlog = await ScrimsBanLog.get_or_none(guild_id=interaction.guild_id)
        for user in users_to_ban:
            if await ScrimsBannedUser.filter(user_id=user.id, guild_id=interaction.guild_id).exists():
                continue

            record = await ScrimsBannedUser.create(
                user_id=user.id,
                guild_id=interaction.guild_id,
                banned_till=banned_until,
                reason=modal.ban_reason.value,
                banned_by=interaction.user.id,
            )
            banned_count += 1

            if scrim_banlog:
                self.view.bot.loop.create_task(scrim_banlog.log_ban(record))

            if record.banned_till:
                self.view.bot.loop.create_task(
                    self.view.bot.reminders.create_timer(
                        record.banned_till,
                        "scrim_ban",
                        ban_id=record.id,
                    )
                )

        await interaction.followup.send(embed=self.view.bot.success_embed(f"Banned {banned_count} users from scrims."), ephemeral=True)
        await self.view.refresh_view()


class UnbanUsers(ScrimsBtn):
    view: ScrimBanManager

    def __init__(self, ctx: commands.Context, disabled: bool = True):
        super().__init__(ctx, disabled=disabled, style=discord.ButtonStyle.green, label="Unban Users")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        banned_users = await ScrimsBannedUser.filter(guild_id=self.ctx.guild.id).order_by("id")
        if not banned_users:
            return await interaction.followup.send(embed=self.view.bot.error_embed("No teams are banned."), ephemeral=True)

        view = ScrimsView(self.ctx)
        for banned_users_group in discord.utils.as_chunks(banned_users, 25):
            view.add_item(BannedUserSelector(banned_users_group))

        view.message = await interaction.followup.send("", view=view, ephemeral=True)
        await view.wait()

        await view.message.delete(delay=0)

        if not view.selected_user_ids:
            return

        banlog_record = await ScrimsBanLog.get_or_none(guild_id=self.ctx.guild.id)
        for user_id in view.selected_user_ids:
            banned_user = await ScrimsBannedUser.get_or_none(id=user_id)
            if not banned_user:
                continue

            await banned_user.delete()
            if banlog_record:
                self.view.bot.loop.create_task(banlog_record.log_unban(banned_user, interaction.user))

        await interaction.followup.send(embed=self.view.bot.success_embed("Unbanned selected users."), ephemeral=True)
        await self.view.refresh_view()


class BannedUserInfo(ScrimsBtn):
    view: ScrimBanManager

    def __init__(self, ctx: commands.Context, disabled: bool = True):
        super().__init__(ctx, disabled=disabled, label="Info", emoji=INFO)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        banned_users = await ScrimsBannedUser.filter(guild_id=self.ctx.guild.id).order_by("id")
        if not banned_users:
            return await interaction.followup.send(embed=self.view.bot.error_embed("No users are banned."), ephemeral=True)

        view = ScrimsView(self.ctx)
        for banned_user_group in discord.utils.as_chunks(banned_users, 25):
            view.add_item(BannedUserSelector(banned_user_group, multiple=False, placeholder="Select a banned user to view info ..."))

        view.message = await interaction.followup.send("", view=view, ephemeral=True)
        await view.wait()

        await view.message.delete(delay=0)

        if not view.selected_user_ids:
            return

        banned_user = await ScrimsBannedUser.get_or_none(id=view.selected_user_ids[0])
        if not banned_user:
            return await interaction.followup.send(embed=self.view.bot.error_embed("User not found."), ephemeral=True)

        user = await self.view.bot.get_or_fetch_member(self.ctx.guild, banned_user.user_id)

        embed = discord.Embed(color=self.view.bot.color, timestamp=banned_user.banned_at)
        embed.set_author(
            name=getattr(user, "name", "Unknown User") + f" [{banned_user.user_id}]",
            icon_url=user.display_avatar.url if user else None,
        )
        embed.add_field(
            name="Banned Till",
            value=discord.utils.format_dt(banned_user.banned_till, "R") if banned_user.banned_till else "Never",
            inline=False,
        )
        embed.add_field(name="Reason", value=banned_user.reason or "No reason provided.", inline=False)
        embed.add_field(
            name="Banned By", value=getattr(self.ctx.guild.get_member(banned_user.banned_by), "mention", "Unknown User"), inline=False
        )
        embed.set_footer(text=f"Banned on")
        await interaction.followup.send(embed=embed, ephemeral=True)


class SetBanlogChannel(ScrimsBtn):
    def __init__(self, ctx: commands.Context, row: int = 2):
        super().__init__(ctx, style=discord.ButtonStyle.blurple, label="Set Banlog Channel", row=row)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        channel = await text_channel_input(
            interaction,
            message="Please select the channel where you want to log scrims ban/unban actions.",
        )
        if not channel:
            return

        await ScrimsBanLog.update_or_create(guild_id=interaction.guild_id, defaults={"channel_id": channel.id})
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"Successfully set the ban/unban log channel to {channel.mention}.", color=self.view.bot.color
            ),
            ephemeral=True,
        )

        await self.view.refresh_view()


class BannedUserSelector(discord.ui.Select):
    view: ScrimsView

    def __init__(self, users: list[ScrimsBannedUser], multiple: bool = True, placeholder: str = "Select the players to Unban..."):
        options = []

        for u in users:
            options.append(
                discord.SelectOption(
                    label=f"{getattr(u.user,'name','unknown-user')} [{u.user_id}]",
                    description=f"Expires: {u.banned_till.strftime('%d %b %Y %H:%M') if u.banned_till else 'Never'}",
                    emoji=TEXT_CHANNEL,
                    value=u.id,
                )
            )

        super().__init__(placeholder=placeholder, options=options, max_values=len(options) if multiple else 1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        self.view.selected_user_ids = self.values
        self.view.stop()


class BanFieldsInput(discord.ui.Modal, title="Ban Time & Reason"):
    ban_until = discord.ui.TextInput(
        label="Ban Duration (Optional)",
        placeholder="Eg: 7d, 1d, 24h, etc.",
        max_length=256,
        required=False,
        style=discord.TextStyle.short,
    )

    ban_reason = discord.ui.TextInput(
        label="Reason for Ban (Optional)",
        placeholder="khelne nahi aaye harami :)",
        max_length=200,
        required=False,
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
