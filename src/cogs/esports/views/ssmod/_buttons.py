from __future__ import annotations

from core import Context

from utils import keycap_digit as kd, inputs, truncate_string, BaseSelector, Prompt
import discord
from ._type import SStypeSelector

from constants import SSType
from models import SSVerify


class SetChannel(discord.ui.Button):
    def __init__(self, ctx: Context):
        super().__init__(emoji=kd(1))

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _m = await self.ctx.simple("Mention the channel you want to use for ssverification.")
        channel = await inputs.channel_input(self.ctx, delete_after=True)

        await self.ctx.safe_delete(_m)

        if await SSVerify.filter(pk=channel.id).exists():
            return await self.ctx.error(f"{channel.mention} is already a ssverification channel.", 3)

        if not channel.permissions_for(self.ctx.guild.me).embed_links:
            return await self.ctx.error(f"I need `embed_links` permission in {channel.mention}", 3)

        self.view.record.channel_id = channel.id
        self.ctx.bot.cache.ssverify_channels.add(channel.id)

        await self.view.refresh_view()


class SetRole(discord.ui.Button):
    def __init__(self, ctx: Context):
        super().__init__(emoji=kd(2))
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _m = await self.ctx.simple("Mention the role you want to give for ssverification.")
        role = await inputs.role_input(self.ctx, delete_after=True)

        await self.ctx.safe_delete(_m)
        self.view.record.role_id = role.id

        await self.view.refresh_view()


class RequiredSS(discord.ui.Button):
    def __init__(self, ctx: Context):
        super().__init__(emoji=kd(3))

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _m = await self.ctx.simple("How many screenshots do you need me to verify?")
        _ss = await inputs.integer_input(self.ctx, delete_after=True)

        await self.ctx.safe_delete(_m)
        self.view.record.required_ss = _ss

        await self.view.refresh_view()


class ScreenshotType(discord.ui.Button):
    def __init__(self, ctx: Context):
        super().__init__(emoji=kd(4))

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _v = BaseSelector(self.ctx.author.id, SStypeSelector)
        _m = await self.ctx.simple("What type of screenshots do you want to verify?", view=_v)
        await _v.wait()
        await _m.delete()
        if _v.custom_id:
            self.view.record.ss_type = SSType(_v.custom_id)

            # if not self.view.record.ss_type == SSType.yt:
            #     if not await self.ctx.is_premium_guild():
            #         return await self.ctx.error("You need Quotient Prime to set this filter. (Use `qperks`)", 4)

            if _v.custom_id == "custom":

                _m = await self.ctx.simple(
                    "What name do want to give this filter?\n\n" "Enter any name relevant to what you want to verify.\n"
                )
                _name = await inputs.string_input(self.ctx, delete_after=True)
                await self.ctx.safe_delete(_m)
                _name = truncate_string(_name, max_length=50)

                _m = await self.ctx.simple(
                    "What words might appear in the screenshot? Maybe like name of the game/app or "
                    "anything that you believe to be common in the screenshots.\n\n"
                    "*Separate with comma `,`*"
                )
                _keys = await inputs.string_input(self.ctx, delete_after=True)
                await self.ctx.safe_delete(_m)

                _keys = _keys.split(",")
                self.view.record.keywords = [_name, *[truncate_string(i, 50).strip() for i in _keys]]

                from ._edit import SSmodEditor

                if isinstance(self.view, SSmodEditor):
                    await self.ctx.bot.db.execute(
                        "UPDATE ss_info SET keywords = $2 WHERE id = $1", self.view.record.id, self.view.record.keywords
                    )

                self.view.record.channel_name = _name

                await self.ctx.success(
                    f"Successfully set custom filter.\nKeywords: `{', '.join(self.view.record.keywords)}`", 4
                )

        await self.view.refresh_view()


class PageName(discord.ui.Button):
    def __init__(self, ctx: Context):
        super().__init__(emoji=kd(5))

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _m = await self.ctx.simple("Enter the exact name of your page/channel.")
        _name = await inputs.string_input(self.ctx, delete_after=True)

        await self.ctx.safe_delete(_m)
        self.view.record.channel_name = truncate_string(_name, 30)
        await self.view.refresh_view()


class PageLink(discord.ui.Button):
    def __init__(self, ctx: Context):
        super().__init__(emoji=kd(6))

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _m = await self.ctx.simple("Enter the direct link to your page/channel.")
        _name = await inputs.string_input(self.ctx, delete_after=True)

        await self.ctx.safe_delete(_m)
        self.view.record.channel_link = truncate_string(_name, 130)
        await self.view.refresh_view()


class AllowSame(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji=kd(7))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.record.allow_same = not self.view.record.allow_same
        await self.view.refresh_view()


class SuccessMessage(discord.ui.Button):
    def __init__(self, ctx, **kwargs):
        super().__init__(emoji=kd(8), **kwargs)

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        m = await self.ctx.simple(
            "What message do you want me to show for successful verification? This message will be sent to "
            "DM of players who verify screenshots successfully.\n\n**Current Success Message:**"
            f"```{self.view.record.success_message if self.view.record.success_message else 'Not Set Yet.'}```"
            "\n`Kindly keep it under 500 characters. Enter none to remove it.`"
        )

        msg = await inputs.string_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)

        msg = truncate_string(msg, 500)
        if msg.lower().strip() == "none":
            msg = None
            await self.ctx.success("Removed Success Message.", 3)

        elif msg.lower().strip() == "cancel":
            return

        if msg != None:
            await self.ctx.success("Success Message Updated.", 3)

        self.view.record.success_message = msg
        await self.view.refresh_view()


class DeleteButton(discord.ui.Button):
    def __init__(self, ctx: Context, record: SSVerify):
        super().__init__(label="Delete ssverify", style=discord.ButtonStyle.red)
        self.ctx = ctx
        self.record = record

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        prompt = await self.ctx.prompt("Are you sure you want to delete this ssverify?")
        if not prompt:
            return await self.ctx.simple("Okay, not deleting.", 3)

        await self.record.full_delete()
        await self.ctx.success("Successfully deleted ssverify.", 3)
        return await self.view.on_timeout()


class DiscardButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Discard", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        return await self.view.on_timeout()


class SaveButton(discord.ui.Button):
    def __init__(self, ctx: Context):
        self.ctx = ctx
        super().__init__(label="Save & Setup", style=discord.ButtonStyle.green, disabled=True)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        await self.view.record.save()
        self.ctx.bot.cache.ssverify_channels.add(self.view.record.channel_id)
        await self.view.on_timeout()
        await self.ctx.success(f"Successfully set ssverification in {self.view.record.channel.mention}.", 3)
