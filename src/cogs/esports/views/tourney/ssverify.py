from __future__ import annotations

from ...views.base import EsportsBaseView
from core import Context
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core import Quotient

from utils import regional_indicator as ri, inputs, truncate_string
from models import SSVerify, SSData
import discord
from string import ascii_uppercase

from constants import SSType


class SsVerifyEditor(EsportsBaseView):
    def __init__(self, ctx: Context, model: SSVerify):
        super().__init__(ctx, timeout=30, title="Screenshot-Moderator")

        self.model = model
        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    @staticmethod
    def initial_embed(record: SSVerify) -> discord.Embed:
        _e = discord.Embed(color=0x00FFB3, title="Screenshot-Mod Editor")

        fields = {
            "Channel": getattr(record.channel, "mention", "`Not-Found`"),
            "Role": getattr(record.role, "mention", "`Not-Found`"),
            "Required ss": f"`{record.required_ss}`",
            "Page Name": f"`{record.channel_name}`",
            "Page URL": f"[Click Here]({record.channel_link})",
            "Page Type": f"`{record.ss_type.value.title()}`",
            "Success Message": f"`Click Button`",
        }

        for idx, (name, value) in enumerate(fields.items()):
            _e.add_field(
                name=f"{ri(ascii_uppercase[idx])} {name}:",
                value=value,
            )

        return _e

    async def __update_model(self, **kwargs):
        await SSVerify.filter(pk=self.model.pk).update(**kwargs)
        await self.__refresh_view()

    async def __refresh_view(self):
        await self.model.refresh_from_db()
        embed = self.initial_embed(self.model).set_thumbnail(url=self.bot.user.avatar.url)
        try:
            self.message = await self.message.edit(embed=embed, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    @discord.ui.button(emoji=ri("A"), custom_id="ssverify_channel")
    async def set_channel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        m = await self.ask_embed("Kindly enter the new channel for ssverification.\n\n`Mention of enter its ID.`")
        channel = await inputs.channel_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(m)

        self.bot.cache.ssverify_channels.discard(self.model.channel_id)
        self.bot.cache.ssverify_channels.add(channel.id)

        await self.__update_model(channel_id=channel.id)

    @discord.ui.button(emoji=ri("B"), custom_id="ssverify_role")
    async def set_role(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        m = await self.ask_embed(
            "Which role do you want me to give for successful verification?\n\n`Mention the role or enter ID.`"
        )
        role = await inputs.role_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(m)
        await self.__update_model(role_id=role.id)

    @discord.ui.button(emoji=ri("C"), custom_id="ssverify_ss")
    async def set_required_ss(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        m = await self.ask_embed(
            "How many screenshots are required for verification?\n\n`Enter a number between 1 and 10.`"
        )
        required_ss = await inputs.integer_input(self.ctx, self.check, delete_after=True, limits=(1, 10))
        await self.ctx.safe_delete(m)

        await self.__update_model(required_ss=required_ss)

    @discord.ui.button(emoji=ri("D"), custom_id="ssverify_name")
    async def set_name(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        m = await self.ask_embed(
            f"Kindly enter the new name of your {self.model.ss_type.value.title()} page.\n\n`Max length is 20.`"
        )
        name = await inputs.string_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(m)
        await self.__update_model(channel_name=name)

    @discord.ui.button(emoji=ri("E"), custom_id="ssverify_link")
    async def set_link(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        m = await self.ask_embed(f"What is the link of your {self.model.ss_type.value.title()} page?")
        link = await inputs.string_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(m)
        await self.__update_model(channel_link=link)

    @discord.ui.button(emoji=ri("F"), custom_id="ssverify_type")
    async def set_type(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.__update_model(ss_type=SSType.yt if self.model.ss_type == SSType.insta else SSType.insta)

    @discord.ui.button(emoji=ri("G"), custom_id="ssverify_message")
    async def set_message(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        m = await self.ask_embed(
            "What message do you want me to show for successful verification? This message will be sent to "
            "DM of players who verify screenshots successfully.\n\n**Current Success Message:**"
            f"```{self.model.success_message if self.model.success_message else 'Not Set Yet.'}```"
            "\n`Kindly keep it under 500 characters. Enter none to remove it.`"
        )

        msg = await inputs.string_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(m)

        msg = truncate_string(msg, 500)
        if msg.lower().strip() == "none":
            msg = None
            await self.ctx.success("Removed Success Message.", 3)

        elif msg.lower().strip() == "cancel":
            return

        if msg != None:
            await self.ctx.success("Success Message Updated.", 3)

        await self.__update_model(success_message=msg)

    @discord.ui.button(custom_id="ssverify_stop", label="Stop Editing", style=discord.ButtonStyle.green)
    async def stop_editor(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.on_timeout()

    @discord.ui.button(custom_id="ssverify_delete", label="Delete Setup", style=discord.ButtonStyle.red)
    async def delete_ssverify(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        prompt = await self.ctx.prompt("Are you sure you want to delete this setup?\n\n`This action cannot be undone.`")
        if not prompt:
            return await self.ctx.simple("Alright, Aborting", 3)


        await self.model.full_delete()
        await self.ctx.success("SSverification setup deleted.")
        await self.on_timeout()
