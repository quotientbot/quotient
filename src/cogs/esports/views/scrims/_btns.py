from __future__ import annotations

from datetime import timedelta

import discord
from discord import Interaction

from core import Context
from models import Scrim
from utils import discord_timestamp as dt, inputs, regional_indicator as ri, truncate_string, emote

from ._base import ScrimsButton


class SetName(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        m = await self.ctx.simple("Enter the new name of this scrim. (`Max 30 characters`)")
        name = await inputs.string_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)
        self.view.record.name = truncate_string(name, 30)

        await self.view.refresh_view()


class RegChannel(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        m = await self.ctx.simple("Mention the channel where you want to take registrations.")
        channel = await inputs.channel_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)

        if await Scrim.filter(registration_channel_id=channel.id).exists():
            return await self.ctx.error("That channel is already in use for another scrim.", 5)

        self.view.record.registration_channel_id = channel.id

        if not self.view.record.slotlist_channel_id:
            self.view.record.slotlist_channel_id = channel.id

        await self.view.refresh_view()


class SlotChannel(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        m = await self.ctx.simple("Mention the channel where you want me to post slotlist after registrations.")
        channel = await inputs.channel_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)

        self.view.record.slotlist_channel_id = channel.id

        await self.view.refresh_view()


class SetRole(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        m = await self.ctx.simple("Mention the role you want to give for correct registration.")
        role = await inputs.role_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)

        self.view.record.role_id = role.id

        await self.view.refresh_view()


class SetMentions(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        m = await self.ctx.simple("How many mentions are required for registration? (Max `10`)")
        self.view.record.required_mentions = await inputs.integer_input(self.ctx, delete_after=True, limits=(0, 10))
        await self.ctx.safe_delete(m)

        await self.view.refresh_view()


class TotalSlots(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        m = await self.ctx.simple("How many total slots are there? (Max `30`)")
        self.view.record.total_slots = await inputs.integer_input(self.ctx, delete_after=True, limits=(1, 30))
        await self.ctx.safe_delete(m)

        await self.view.refresh_view()


class OpenTime(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        m = await self.ctx.simple(
            "At what time do you want me to open registrations daily?\n\nTime examples:",
            image="https://cdn.discordapp.com/attachments/851846932593770496/958291942062587934/timex.gif",
            footer="Time is according to Indian Standard Time (UTC+05:30)",
        )
        self.view.record.open_time = await inputs.time_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)

        await self.view.refresh_view()


class SetEmojis(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        if not await self.ctx.is_premium_guild():
            return await self.ctx.error(
                "[Quotient Premium](https://quotientbot.xyz/premium) is required to use this feature.", 4
            )

        e = discord.Embed(color=self.ctx.bot.color, title="Edit scrims emojis")

        e.description = (
            "Which emojis do you want to use for tick and cross in scrims registrations?\n\n"
            "`Please enter two emojis and separate them with a comma`"
        )

        e.set_image(url="https://cdn.discordapp.com/attachments/851846932593770496/888097255607906354/unknown.png")
        e.set_footer(text="The first emoji must be the emoji for tick mark.")

        m = await interaction.followup.send(embed=e)
        emojis = await inputs.string_input(self.ctx, delete_after=True)

        await self.ctx.safe_delete(m)

        emojis = emojis.strip().split(",")
        if not len(emojis) == 2:
            return await interaction.followup.send("You didn't enter the correct format.", ephemeral=True)

        check, cross = emojis

        for emoji in emojis:
            try:
                await self.view.message.add_reaction(emoji.strip())
                await self.view.message.clear_reactions()
            except discord.HTTPException:
                return await interaction.followup.send("One of the emojis you entered is invalid.", ephemeral=True)

        self.view.record.emojis = {"tick": check.strip(), "cross": cross.strip()}
        await self.view.refresh_view()
        await self.view.record.confirm_all_scrims(self.ctx, emojis=self.view.record.emojis)


class SetAutoclean(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        from ._ac import AutocleanView

        self.view.stop()

        view = AutocleanView(self.ctx, self.view.record)
        view.message = await self.view.message.edit(embed=view.initial_embed, view=view)


class PingRole(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class OpenRole(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class OpenDays(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        from ._days import WeekDays

        await interaction.response.defer()
        v = discord.ui.View(timeout=60.0)
        v.add_item(WeekDays())

        await interaction.followup.send("Please select the days to open registrations:", view=v, ephemeral=True)
        await v.wait()
        if c := getattr(v, "custom_id", None):
            self.view.record.open_days = c
            await self.view.refresh_view()


class MultiReg(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        self.view.record.multiregister = not self.view.record.multiregister
        await self.ctx.success(
            f"Now users **{'can' if self.view.record.multiregister else 'can not'}** register more than once.", 3
        )
        await self.view.refresh_view()

        await self.view.record.confirm_all_scrims(self.ctx, multiregister=self.view.record.multiregister)


class TeamCompulsion(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        self.view.record.teamname_compulsion = not self.view.record.teamname_compulsion
        await self.ctx.success(
            f"Now Team Name **{'is' if self.view.record.teamname_compulsion else 'is not'}** required to register.", 3
        )
        await self.view.refresh_view()
        await self.view.record.confirm_all_scrims(self.ctx, teamname_compulsion=self.view.record.teamname_compulsion)


class DuplicateTeam(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        self.view.record.no_duplicate_name = not self.view.record.no_duplicate_name
        await self.ctx.success(
            f"Duplicate team names are now **{'not allowed' if self.view.record.no_duplicate_name else 'allowed'}**.", 3
        )
        await self.view.refresh_view()

        await self.view.record.confirm_all_scrims(self.ctx, no_duplicate_name=self.view.record.no_duplicate_name)


class DeleteReject(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        self.view.record.autodelete_rejects = not self.view.record.autodelete_rejects
        await self.ctx.success(
            f"Rejected registrations will **{'be' if self.view.record.autodelete_rejects else 'not be'}** deleted automatically.",
            3,
        )
        await self.view.refresh_view()
        await self.view.record.confirm_all_scrims(self.ctx, autodelete_rejects=self.view.record.autodelete_rejects)


class DeleteLate(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        self.view.record.autodelete_extras = not self.view.record.autodelete_extras
        await self.ctx.success(
            f"Late/Extra registration messages will **{'be' if self.view.record.autodelete_extras else 'not be'}** deleted automatically.",
            3,
        )
        await self.view.refresh_view()
        await self.view.record.confirm_all_scrims(self.ctx, autodelete_extras=self.view.record.autodelete_extras)


class SlotlistStart(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        m = await self.ctx.success(
            f"From which slot number do you want to start the slotlist? (Enter a number between 1 and {self.view.record.total_slots})"
        )
        self.view.record.start_from = await inputs.integer_input(
            self.ctx, delete_after=True, limits=(1, self.view.record.total_slots)
        )

        await self.ctx.safe_delete(m)
        await self.view.refresh_view()
        await self.view.record.confirm_all_scrims(self.ctx, start_from=self.view.record.start_from)


class Discard(ScrimsButton):
    def __init__(self, ctx: Context, label="Back", row: int = None):
        super().__init__(style=discord.ButtonStyle.red, label=label, row=row)
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        from .main import ScrimsMain as SM

        self.view.stop()
        v = SM(self.ctx)
        v.message = await self.view.message.edit(embed=await v.initial_embed(), view=v)


class DeleteScrim(ScrimsButton):
    def __init__(self, ctx: Context):
        super().__init__(emoji=emote.trash, label="Delete")
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        prompt = await self.ctx.prompt(
            f"{self.view.record} will be permanently deleted. This action is irreversible.",
            title="Are you sure you want to continue?",
        )
        if not prompt:
            return await self.ctx.simple("OK! Not deleting.", 4)

        await self.view.record.full_delete()
        await self.ctx.success(f"{self.view.record} has been deleted.", 4)

        from .main import ScrimsMain as SM

        self.view.stop()
        v = SM(self.ctx)
        v.message = await self.view.message.edit(embed=await v.initial_embed(), view=v)


class SaveScrim(ScrimsButton):
    def __init__(self, ctx: Context):
        super().__init__(style=discord.ButtonStyle.green, label="Save Scrim", disabled=True)
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        self.ctx.bot.loop.create_task(self.view.record.setup_logs())

        self.view.record.autoclean_time = self.ctx.bot.current_time.replace(
            hour=4, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        await self.view.record.save()

        await self.ctx.bot.reminders.create_timer(self.view.record.open_time, "scrim_open", scrim_id=self.view.record.id)

        await self.ctx.bot.reminders.create_timer(
            self.view.record.autoclean_time, "autoclean", scrim_id=self.view.record.id
        )

        self.view.stop()
        await self.ctx.success(f"Scrim was successfully created. (Registration: {dt(self.view.record.open_time)})", 6)

        from .main import ScrimsMain

        view = ScrimsMain(self.ctx)
        view.message = await self.view.message.edit(embed=await view.initial_embed(), view=view)


#!add option to add this scrim to cancel claim
