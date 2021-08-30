from models import Scrim, AssignedSlot, ArrayAppend
from utils import integer_input, string_input, QuoMember, truncate_string

from async_property import async_property
from core import Context
from contextlib import suppress

from ..helpers import update_main_message
import discord


__all__ = ("SlotlistEditor",)


class SlotlistEditor(discord.ui.View):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(timeout=90.0)

        self.scrim = scrim
        self.ctx = ctx
        self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "Sorry, you can't use this interaction as it is not started by you.", ephemeral=True
            )
            return False
        return True

    async def ask_embed(self, desc: str, *, image=None):
        embed = discord.Embed(color=self.ctx.bot.color, description=desc, title="Slotlist Editor")
        if image:
            embed.set_image(url=image)
        return await self.ctx.send(embed=embed)

    async def error_embed(self, desc: str):
        embed = discord.Embed(color=discord.Color.red(), title="Whoopsi-Doopsi", description=desc)
        await self.ctx.send(embed=embed, delete_after=2)

    async def on_timeout(self) -> None:
        if hasattr(self, "message"):
            for b in self.children:

                b.style, b.disabled = discord.ButtonStyle.grey, True

            await self.message.edit(embed=await self.updated_embed, view=self)

    async def refresh(self):
        _embed = await self.updated_embed
        await self.message.edit(embed=_embed, view=self)

        if self.scrim.slotlist_message_id:
            msg = await self.scrim.slotlist_channel.fetch_message(self.scrim.slotlist_message_id)
            if msg:
                return await msg.edit(embed=_embed)

        return await self.scrim.slotlist_channel.send(embed=_embed)

    @async_property
    async def updated_embed(self):
        embed, channel = await self.scrim.create_slotlist()
        return embed

    @discord.ui.button(style=discord.ButtonStyle.success, custom_id="replace", label="Replace Slot")
    async def replace_a_slot(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        m = await self.ask_embed("Which slot do you want to replace?\n\n`Please enter the slot number.`")

        input = await integer_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(m)

        slot = await self.scrim.assigned_slots.filter(num=input).first()
        if not slot:
            await self.error_embed("The slot number you entered was invalid. Please try again.")
            return await self.refresh()

        m = await self.ask_embed(
            "Please mention the user to give slot and enter their team name.\n\n"
            "`Mention the player first then write team name`. Separate them with comma (,)",
            image="https://cdn.discordapp.com/attachments/851846932593770496/881913489365532702/unknown.png",
        )

        info = await string_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(m)

        info = info.strip().split(",")
        if not len(info) == 2:
            await self.error_embed("You had to mention the user first, then the team name. Your format wasn't correct.")

        user, team_name = info

        user = await QuoMember().convert(self.ctx, user)
        team_name = truncate_string(team_name, 22)
        await AssignedSlot.filter(pk=slot.id).update(user_id=user.id, team_name=team_name.strip())

        with suppress(AttributeError, discord.Forbidden, discord.HTTPException):
            user = self.ctx.guild.get_member(slot.user_id)
            if user:
                await user.remove_roles(discord.Object(id=self.scrim.role_id))

            await user.add_roles(discord.Object(id=self.scrim.role_id))

        await self.refresh()

    @discord.ui.button(style=discord.ButtonStyle.success, custom_id="add", label="Add Slot")
    async def add_a_slot(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        m = await self.ask_embed(
            "Please mention the user to give slot and enter their team name.\n\n"
            "`Mention the player first then write team name`. Separate them with comma (,)",
            image="https://cdn.discordapp.com/attachments/851846932593770496/881913489365532702/unknown.png",
        )

        info = await string_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(m)

        info = info.strip().split(",")
        if not len(info) == 2:
            await self.error_embed("You had to mention the user first, then the team name. Your format wasn't correct.")

        user, team_name = info

        user = await QuoMember().convert(self.ctx, user)
        team_name = truncate_string(team_name, 22)

        assigned_slots = await self.scrim.assigned_slots.order_by("-num").first()
        slot = await AssignedSlot.create(
            user_id=self.ctx.author.id,
            team_name=team_name.strip(),
            num=assigned_slots.num + 1,
            jump_url=self.ctx.message.jump_url,
        )

        await self.scrim.assigned_slots.add(slot)
        await self.refresh()

    @discord.ui.button(style=discord.ButtonStyle.red, custom_id="remove", label="Remove Slot")
    async def remove_a_slot(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        m = await self.ask_embed("Which slot do you want to remove?\n\n`Please enter the slot number.`")
        input = await integer_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(m)

        slot = await self.scrim.assigned_slots.filter(num=input).first()
        if not slot:
            await self.error_embed("The slot number you entered was invalid. Please try again.")
            return await self.refresh()

        with suppress(AttributeError, discord.Forbidden, discord.HTTPException):
            user = self.ctx.guild.get_member(slot.user_id)
            if user:
                await user.remove_roles(discord.Object(id=self.scrim.role_id))

        await Scrim.filter(pk=self.scrim.id).update(available_slots=ArrayAppend("available_slots", slot.num))
        await AssignedSlot.filter(pk=slot.id).delete()

        await update_main_message(self.ctx.guild.id)
        await self.refresh()
