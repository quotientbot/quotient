import discord
from discord.ext import commands
from lib import EXIT, keycap_digit, plural

from quotient.models import DayType, Guild, MapType, Scrim

from .. import ScrimsBtn, ScrimsView
from ..utility.buttons import DiscardChanges
from ..utility.common import get_scrim_position
from ..utility.paginator import NextScrim, PreviousScrim, SkipToScrim
from ..utility.selectors import prompt_scrims_selector


class SelectMap(discord.ui.Select):
    def __init__(self, day: DayType):
        _o = []
        for idx, m in enumerate(MapType, start=1):
            _o.append(discord.SelectOption(label=m.name.title(), value=m.name, emoji=keycap_digit(idx)))

        super().__init__(placeholder=f"Select the Map for {day.name.title()}", options=_o)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.selected_map = self.values[0]

        self.view.stop()


class SetDayBtnView(ScrimsBtn):
    def __init__(self, ctx: commands.Context, day: DayType, scrim: Scrim):
        super().__init__(ctx, label=day.name.title(), style=discord.ButtonStyle.blurple)
        self.day = day
        self.scrim = scrim

    async def callback(self, interaction: discord.Interaction):

        v = discord.ui.View(timeout=60)
        v.add_item(SelectMap(self.day))

        await interaction.response.send_message("\u200b", view=v, ephemeral=True)
        await v.wait()

        if not v.selected_map:
            return

        self.scrim.game_maps[self.day.name] = v.selected_map
        await self.scrim.save(update_fields=["game_maps"])

        await self.view.refresh_view()

        await interaction.edit_original_response(content=f"Successfully set the map to `{v.selected_map}`", view=None)


class CopySettingsBtn(ScrimsBtn):
    def __init__(self, ctx: commands.Context, scrim: Scrim, disabled: bool = False):
        super().__init__(ctx, label="Copy Settings To ...", style=discord.ButtonStyle.green, emoji="📄", disabled=disabled)
        self.scrim = scrim

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        selected_scrims = await prompt_scrims_selector(
            interaction,
            interaction.user,
            await Scrim.filter(guild_id=interaction.guild_id).order_by("reg_start_time"),
            "Select the scrims to copy settings to ...",
            force_dropdown=True,
        )

        if not selected_scrims:
            return

        await Scrim.filter(id__in=[s.pk for s in selected_scrims]).update(game_maps=self.scrim.game_maps)

        await self.view.refresh_view()
        await interaction.followup.send(
            embed=self.scrim.bot.success_embed(
                f"Successfully copied the settings to the selected `{plural(selected_scrims):scrim|scrims}`."
            ),
            ephemeral=True,
        )


class DeleteSettingsBtn(ScrimsBtn):
    def __init__(self, ctx: commands.Context, scrim: Scrim):
        super().__init__(ctx, label="Delete Settings", style=discord.ButtonStyle.red)
        self.scrim = scrim

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        self.scrim.game_maps = {d.name: None for d in DayType}
        await self.scrim.save(update_fields=["game_maps"])

        await self.view.refresh_view()
        await interaction.followup.send(content=f"Successfully cleared the settings for {self.scrim}.")


class DropLocationSettingsPanel(ScrimsView):
    def __init__(self, ctx: commands.Context, scrim: Scrim):
        super().__init__(ctx=ctx, timeout=100)
        self.ctx = ctx
        self.record = scrim

    async def initial_msg(self) -> discord.Embed:
        scrims = await Scrim.filter(guild_id=self.ctx.guild.id).order_by("reg_start_time")
        self.clear_items()

        for d in DayType:
            self.add_item(SetDayBtnView(self.ctx, d, self.record))

        self.add_item(CopySettingsBtn(self.ctx, self.record, disabled=not scrims))
        self.add_item(DeleteSettingsBtn(self.ctx, self.record))

        if len(scrims) > 1:
            self.add_item(PreviousScrim(self.ctx, row=3))
            self.add_item(SkipToScrim(self.ctx, row=3))
            self.add_item(NextScrim(self.ctx, row=3))

        self.add_item(DiscardChanges(self.ctx, label="Back to Main Menu", emoji=EXIT, row=3))

        embed = discord.Embed(
            color=self.bot.color,
            url=self.bot.config("SUPPORT_SERVER_LINK"),
            title=f"Drop Location Panel - #{self.record.registration_channel}",
        )

        embed.description = "```"
        for idx, d in enumerate(DayType, start=1):
            embed.description += f"{idx}. {d.name.title().ljust(12)} {self.record.game_maps[d.name] or '__'}\n"
        embed.description += "```"

        embed.set_footer(text=f"Page - {' / '.join(await get_scrim_position(self.record.pk, self.ctx.guild.id))}")
        return embed

    async def refresh_view(self):
        try:
            self.message = await self.message.edit(content="", embed=await self.initial_msg(), view=self)
        except discord.HTTPException:
            await self.on_timeout()
