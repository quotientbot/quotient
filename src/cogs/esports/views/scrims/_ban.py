from __future__ import annotations

import asyncio
import typing as T
from contextlib import suppress
from datetime import timedelta

import dateparser
import discord

from core import Context, QuotientView
from models import BanLog, BannedTeam, Scrim
from utils import discord_timestamp, emote, plural, truncate_string

from ._base import ScrimsButton, ScrimsView
from ._btns import Discard
from ._pages import *

__all__ = ("ScrimBanManager",)


class ScrimBanManager(ScrimsView):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(ctx)

        self.ctx = ctx
        self.record = scrim

    @property
    async def initial_message(self):

        banned = [_ async for _ in self.record.banned_teams.all()]

        _e = discord.Embed(color=self.bot.color)
        _e.description = f"**Start / Stop scrim registration of {self.record}**\n\n__Banned:__\n"

        t = ""
        for idx, _ in enumerate(banned, 1):
            t += (
                f"`{idx:02}.` {getattr(self.bot.get_user(_.user_id),'mention','`unknown-user`')} "
                f"`[{_.user_id}]` - {discord_timestamp(_.expires) if _.expires else 'Lifetime'}\n"
            )

        if t != "":
            _e.description += truncate_string(t, 3900)
        else:
            _e.description += "```\nNo Banned user\n```"

        _e.set_author(name=f"Page - {' / '.join(await self.record.scrim_posi())}", icon_url=self.bot.user.avatar.url)

        return _e

    async def refresh_view(self):
        await self._add_buttons()
        try:
            self.message = await self.message.edit(embed=await self.initial_message, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    async def _add_buttons(self):
        self.clear_items()

        self.add_item(Ban())
        self.add_item(UnBan())
        self.add_item(UnbanAll())

        if await Scrim.filter(guild_id=self.ctx.guild.id).count() >= 2:
            self.add_item(Prev(self.ctx, 2))
            self.add_item(SkipTo(self.ctx, 2))
            self.add_item(Next(self.ctx, 2))

        self.add_item(Discard(self.ctx, "Main Menu", 2))


class Ban(ScrimsButton):
    def __init__(self):
        super().__init__(label="Ban Users", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        modal = MainInput()
        await interaction.response.send_modal(modal)
        await modal.wait()

        m = await self.view.ctx.simple("Please mention the users to ban from this scrim.")
        try:
            msg: discord.Message = await self.view.bot.wait_for(
                "message",
                check=lambda x: x.author.id == interaction.user.id and x.channel.id == interaction.channel_id,
                timeout=60.0,
            )
        except asyncio.TimeoutError:
            await self.view.ctx.safe_delete(m)
            return await self.view.ctx.error("Time out, Please try again later.", 5)

        await self.view.ctx.safe_delete(m)
        await self.view.ctx.safe_delete(msg)

        if not (user_ids := msg.raw_mentions):
            return await self.view.ctx.error("You didn't mention any user to ban.", 5)

        expires = None
        if modal.m_time.value:
            with suppress(TypeError):
                expires = dateparser.parse(
                    modal.m_time.value,
                    settings={
                        "RELATIVE_BASE": self.view.ctx.bot.current_time,
                        "TIMEZONE": "Asia/Kolkata",
                        "RETURN_AS_TIMEZONE_AWARE": True,
                    },
                )

                while self.view.bot.current_time > expires:
                    expires = expires + timedelta(hours=24)

        count = 0
        for user_id in user_ids:
            if await self.view.record.banned_teams.filter(user_id=user_id).exists():
                continue

            b = await BannedTeam.create(user_id=user_id, expires=expires, reason=modal.m_reason.value)
            await self.view.record.banned_teams.add(b)

            if banlog := await BanLog.get_or_none(guild_id=interaction.guild_id):
                await banlog.log_ban(user_id, interaction.user, [self.view.record], modal.m_reason.value, expires)

            if expires:

                await self.view.bot.reminders.create_timer(
                    expires,
                    "scrim_ban",
                    scrims=[self.view.record.id],
                    user_id=user_id,
                    mod=interaction.user.id,
                    reason=modal.m_reason.value,
                )
            count += 1

        await self.view.ctx.success(f"Successfuly banned `{plural(count):user|users}` from {self.view.record}.", 6)
        return await self.view.refresh_view()


class UnBan(ScrimsButton):
    def __init__(self):
        super().__init__(label="Unban Users", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not (banned_teams := await self.view.record.banned_teams.order_by("id")):
            return await self.view.ctx.error("No banned user found.", 5)

        v = QuotientView(self.view.ctx)
        v.add_item(BanSelector(self.view.ctx, banned_teams[:25]))
        v.message = await interaction.followup.send("", view=v, ephemeral=True)
        await v.wait()
        if v.custom_id:
            banlog = await BanLog.get_or_none(guild_id=interaction.guild_id)

            for b in v.custom_id:
                slot = await BannedTeam.get_or_none(pk=b)
                if not slot:
                    continue

                await slot.delete()

                if banlog:
                    await banlog.log_unban(
                        slot.user_id, self.view.ctx.author, [self.view.record], "```No reason given```"
                    )

        await self.view.ctx.success(f"Successfully unbanned `{plural(v.custom_id):user|users}`.", 6)
        return await self.view.refresh_view()


class UnbanAll(ScrimsButton):
    def __init__(self):
        super().__init__(label="Unban All", style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        scrims = await Scrim.show_selector(self.view.ctx, multi=True)

        scrims = [scrims] if not isinstance(scrims, list) else scrims

        prompt = await self.view.ctx.prompt(f"Every banned user will be unbanned from `{plural(scrims):scrim|scrims}`")
        if not prompt:
            return await self.view.ctx.error("OK! Aborting.", 4)

        count = 0
        for scrim in scrims:
            bans = await scrim.banned_teams.all()
            await BannedTeam.filter(pk__in=(_.pk for _ in bans)).delete()
            count += len(bans)

        await self.view.ctx.success(f"Unbanned `{plural(count):user|users}` from `{plural(len(scrims)):scrim|scrims}`", 5)
        return await self.view.refresh_view()


class MainInput(discord.ui.Modal, title="Edit Embed Message"):
    m_time = discord.ui.TextInput(
        label="Ban Duration (Optional)",
        placeholder="Eg: 7 days, 1d, 24h, Friday at 6pm, etc.",
        max_length=256,
        required=False,
        style=discord.TextStyle.short,
    )

    m_reason = discord.ui.TextInput(
        label="Reason for Ban (Optional)",
        placeholder="khelne nahi aaye harami :)",
        max_length=256,
        required=False,
        style=discord.TextStyle.short,
    )


class BanSelector(discord.ui.Select):
    view: QuotientView

    def __init__(self, ctx: Context, teams: T.List[BannedTeam]):
        _options = []

        for _ in teams:
            _options.append(
                discord.SelectOption(
                    label=f"{getattr(ctx.bot.get_user(_.user_id),'name','unknown-user')} [{_.user_id}]",
                    description=f"Expires: {_.expires.strftime('%d %b %Y %H:%M') if _.expires else 'Never'}",
                    emoji=emote.TextChannel,
                    value=_.id,
                )
            )

        super().__init__(placeholder="Select the players to Unban...", options=_options, max_values=len(_options))

    async def callback(self, interaction: discord.Interaction):
        self.view.custom_id = self.values
        self.view.stop()
