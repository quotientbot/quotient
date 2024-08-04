import discord
from discord.ext import commands
from lib import CROSS, EXIT, PLANT, TICK, truncate_string

from quotient.cogs.premium import Feature, can_use_feature, prompt_premium_plan
from quotient.models import Guild, Scrim

from . import ScrimsView
from .ban_unban import ScrimBanManager
from .create_scrim import CreateScrimView
from .design_panel import ScrimsDesignPanel
from .drop_panel.settings import DropLocationSettingsPanel
from .edit_scrim import ScrimsEditPanel
from .instant_toggle import InstantToggleView
from .reservations import ScrimReservationsManager
from .slotm.main_panel import SlotmMainPanel
from .utility.buttons import DiscardChanges
from .utility.selectors import prompt_scrims_selector


class ScrimsMainPanel(ScrimsView):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, timeout=100)

    async def initial_msg(self) -> discord.Embed:

        e = discord.Embed(color=0x00FFB3, title="Quotient's Smart Scrims Manager", url=self.bot.config("SUPPORT_SERVER_LINK"))

        scrims_to_show = []
        for idx, record in enumerate(await Scrim.filter(guild_id=self.ctx.guild.id).order_by("reg_start_time"), start=1):
            scrims_to_show.append(
                f"`{idx:02}.` {(CROSS,TICK)[record.scrim_status]}: {str(record)} - {discord.utils.format_dt(record.reg_start_time,'t')}"
            )

        e.description = "\n".join(scrims_to_show) if scrims_to_show else "```Click Create button for new Scrim.```"

        e.description = truncate_string(e.description, 4096)

        e.set_footer(
            text=f"Total Scrims in this server: {len(scrims_to_show)}",
            icon_url=getattr(self.ctx.author.display_avatar, "url", None),
        )

        if not scrims_to_show:
            for i, child in enumerate(self.children):
                if i != 0 and i != len(self.children) - 1:
                    child.disabled = True

        return e

    @discord.ui.button(label="Create Scrim", style=discord.ButtonStyle.primary)
    async def create_new_scrim(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        is_allowed, min_tier = await can_use_feature(Feature.SCRIM_CREATE, inter.guild_id)
        if not is_allowed:
            return await prompt_premium_plan(
                inter,
                f"Your server has reached the limit of scrims allowed. Upgrade to min **__{min_tier.name}__** tier to create more scrims.",
            )

        self.stop()

        v = CreateScrimView(self.ctx)
        v.message = await self.message.edit(content="", embed=v.initial_msg(), view=v)

    @discord.ui.button(label="Edit Settings", style=discord.ButtonStyle.blurple)
    async def edit_scrim_settings(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        scrims = await prompt_scrims_selector(
            inter,
            self.ctx.author,
            await Scrim.filter(guild_id=inter.guild_id),
            placeholder="Select a scrim to edit ...",
            single_scrim_only=True,
        )

        if not scrims:
            return

        self.stop()

        v = ScrimsEditPanel(self.ctx, scrims[0])
        v.message = await self.message.edit(content="", embed=await v.initial_msg(), view=v)

    @discord.ui.button(label="Instant Start/Stop Reg", style=discord.ButtonStyle.secondary)
    async def instant_start_stop_reg(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        scrims = await prompt_scrims_selector(
            inter,
            self.ctx.author,
            await Scrim.filter(guild_id=inter.guild_id),
            placeholder="Select a scrim to start/stop registration ...",
            single_scrim_only=True,
        )

        if not scrims:
            return

        self.stop()
        v = InstantToggleView(self.ctx, scrims[0])
        v.message = await self.message.edit(content="", embed=await v.initial_msg(), view=v)

    @discord.ui.button(label="Manage Slot Reservations", style=discord.ButtonStyle.green)
    async def manage_slot_reservations(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        scrims = await prompt_scrims_selector(
            inter,
            self.ctx.author,
            await Scrim.filter(guild_id=inter.guild_id),
            placeholder="Select a scrim to manage slot reservations ...",
            single_scrim_only=True,
        )

        if not scrims:
            return

        self.stop()
        v = ScrimReservationsManager(self.ctx, scrims[0])
        v.message = await self.message.edit(content="", embed=await v.initial_msg(), view=v)

    @discord.ui.button(label="Ban / Unban Teams", style=discord.ButtonStyle.primary)
    async def ban_unban_teams(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        self.stop()

        v = ScrimBanManager(self.ctx)
        v.message = await self.message.edit(content="", embed=await v.initial_msg(), view=v)

    @discord.ui.button(label="Change Designs", style=discord.ButtonStyle.secondary, emoji=PLANT)
    async def change_designs(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        scrims = await prompt_scrims_selector(
            inter,
            self.ctx.author,
            await Scrim.filter(guild_id=inter.guild_id),
            placeholder="Select a scrim to change designs ...",
            single_scrim_only=True,
        )

        if not scrims:
            return

        self.stop()
        v = ScrimsDesignPanel(self.ctx, scrims[0])
        v.message = await self.message.edit(content="", embed=await v.initial_msg(), view=v)

    @discord.ui.button(label="Enable / Disable Scrims", style=discord.ButtonStyle.danger)
    async def enable_disable_scrims(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        scrims = await prompt_scrims_selector(
            inter,
            self.ctx.author,
            await Scrim.filter(guild_id=inter.guild_id),
            placeholder="Select scrims to enable/disable ...",
            single_scrim_only=False,
        )

        if not scrims:
            return

        self.stop()
        for scrim in scrims:
            scrim.scrim_status = not scrim.scrim_status
            await scrim.save()

        embed = discord.Embed(color=self.bot.color, description="Successfully toggled the status of selected scrims.\n\n")
        for scrim in scrims:
            embed.description += f"- {('`Disabled`','`Enabled`')[scrim.scrim_status]}: {str(scrim)}\n"

        await inter.followup.send(embed=embed, ephemeral=True)

        v = ScrimsMainPanel(self.ctx)
        v.message = await self.message.edit(content="", embed=await v.initial_msg(), view=v)

    @discord.ui.button(label="Delete Scrims", style=discord.ButtonStyle.danger)
    async def delete_scrims(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        scrims = await prompt_scrims_selector(
            inter,
            self.ctx.author,
            await Scrim.filter(guild_id=inter.guild_id).order_by("reg_start_time"),
            placeholder="Select scrims to delete ...",
            single_scrim_only=False,
            force_dropdown=True,
        )

        if not scrims:
            return

        self.stop()
        for scrim in scrims:
            await scrim.full_delete()

        embed = discord.Embed(color=self.bot.color, description="Successfully deleted selected scrims.\n\n")
        for scrim in scrims:
            embed.description += f"- {str(scrim)}\n"

        await inter.followup.send(embed=embed, ephemeral=True)

        v = ScrimsMainPanel(self.ctx)
        v.message = await self.message.edit(content="", embed=await v.initial_msg(), view=v)

    @discord.ui.button(label="Cancel / Claim Panel", style=discord.ButtonStyle.green)
    async def scrims_cancel_claim_panel(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        self.stop()

        v = SlotmMainPanel(self.ctx)
        v.add_item(DiscardChanges(self.ctx, label="Back to Scrims Panel", emoji=EXIT))

        v.message = await self.message.edit(content="", embed=await v.initial_msg(), view=v)

    @discord.ui.button(label="Drop Location Panel", style=discord.ButtonStyle.blurple)
    async def manage_drop_location_panel(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()
        selected_scrims = await prompt_scrims_selector(
            inter,
            self.ctx.author,
            await Scrim.filter(guild_id=inter.guild_id).order_by("reg_start_time"),
            placeholder="Select a scrim to manage drop locations settings...",
            single_scrim_only=True,
            force_dropdown=True,
        )

        self.stop()
        v = DropLocationSettingsPanel(self.ctx, selected_scrims[0])
        v.message = await self.message.edit(embed=await v.initial_msg(), view=v)
