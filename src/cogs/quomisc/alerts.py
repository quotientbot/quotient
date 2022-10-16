from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from core import Cog, embeds, Context, QuotientView
from discord.ext import commands
from datetime import timedelta
from models import Timer, Alert, Prompt
import discord

__all__ = ("QuoAlerts",)


class PromptView(QuotientView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=None)
        self.ctx = ctx


class CreateAlert(discord.ui.Button):
    view: embeds.EmbedBuilder

    def __init__(self, ctx: Context):
        super().__init__(label="Create Alert", style=discord.ButtonStyle.green)
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        await Alert.filter(active=True).update(active=False)
        record = await Alert.create(author_id=interaction.user.id, message=self.view.formatted)
        await self.ctx.bot.reminders.create_timer(record.created_at + timedelta(days=10), "alert", alert_id=record.id)

        await self.ctx.success("Created a new alert with `ID: {}`".format(record.id))


class QuoAlerts(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_command_completion(self, ctx: Context):
        record = await Alert.filter(active=True).order_by("-created_at").first()
        if not record:
            return

        if await record.reads.filter(user_id=ctx.author.id).exists():
            return

        user_prompts = await record.prompts.filter(user_id=ctx.author.id).order_by("-prompted_at")
        if len(user_prompts) >= 3:
            return

        if user_prompts and user_prompts[0].prompted_at > (ctx.bot.current_time - timedelta(minutes=5)):
            return

        _e = discord.Embed(
            color=self.bot.color, title="You have an unread alert!", description="Click `Read Now` to read it."
        )
        _e.set_thumbnail(url="https://cdn.discordapp.com/attachments/851846932593770496/1031240353489109112/alert.gif")
        await ctx.message.reply(embed=_e, view=...)

        prompt = await Prompt.create(user_id=ctx.author.id)
        await record.prompts.add(prompt)

    @Cog.listener()
    async def on_alert_timer_complete(self, timer: Timer):
        record_id = timer.kwargs["alert_id"]
        await Alert.filter(pk=record_id).update(active=False)

    @Cog.listener()
    async def on_alert_reminder_timer_complete(self, timer: Timer):
        ...

    @commands.group(hidden=True, invoke_without_command=True)
    async def alr(self, ctx: Context):
        await ctx.send_help(ctx.command)

    @alr.command(name="list")
    async def alr_list(self, ctx: Context):
        ...

    @alr.command(name="create")
    async def alr_create(self, ctx: Context):
        _v = embeds.EmbedBuilder(ctx, items=[CreateAlert(ctx)])

        await _v.rendor()
