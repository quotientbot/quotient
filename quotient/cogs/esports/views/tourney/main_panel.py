import discord
from cogs.esports.views.tourney.utility.selectors import prompt_tourneys_selector
from cogs.premium import Feature, can_use_feature, prompt_premium_plan
from discord.ext import commands

from quotient.models import Guild, Tourney

from . import TourneyView
from .create_tourney import CreateTourneyView
from .edit_tourney import TourneysEditPanel


class TourneysMainPanel(TourneyView):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, timeout=100)

    async def initial_msg(self) -> discord.Embed:
        records = await Tourney.filter(guild_id=self.ctx.guild.id).order_by("id").prefetch_related("assigned_slots")
        e = discord.Embed(
            color=self.bot.color, title="Quotient's Smart Tourneys Manager", url=self.bot.config("SUPPORT_SERVER_LINK"), description=""
        )

        for idx, record in enumerate(records, start=1):
            e.description += f"`{idx}.` {record} — Slots: `{sum(1 for _ in record.assigned_slots)}/{record.total_slots}`\n"

        if not records:
            e.description += "```Click 'Create' for new tournament```"

            for i, child in enumerate(self.children):  # Disable every btn except first & last.
                if i != 0 and i != len(self.children) - 1:
                    child.disabled = True

        e.set_footer(
            text=f"Total Tourneys in this server: {len(records)}",
            icon_url=getattr(self.ctx.author.display_avatar, "url", None),
        )

        return e

    @discord.ui.button(label="Create Tournament", style=discord.ButtonStyle.primary)
    async def create_new_tourney(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        is_allowed, min_tier = await can_use_feature(Feature.TOURNEY_CREATE, inter.guild_id)
        if not is_allowed:
            return await prompt_premium_plan(
                inter,
                f"Your server has reached the limit of tournaments allowed. Upgrade to min **__{min_tier.name}__** tier to create more tournaments.",
            )

        self.stop()

        v = CreateTourneyView(self.ctx)
        v.message = await self.message.edit(content="", embed=v.initial_msg(), view=v)

    @discord.ui.button(label="Edit Settings", style=discord.ButtonStyle.blurple)
    async def edit_tourney_settings(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        self.stop()
        v = TourneysEditPanel(
            self.ctx,
            tourney=await Tourney.filter(guild_id=inter.guild_id).order_by("id").first(),
            guild=await Guild.get(pk=inter.guild_id),
        )

        v.message = await self.message.edit(content="", embed=await v.initial_msg(), view=v)

    @discord.ui.button(label="Start / Stop Registration", style=discord.ButtonStyle.success)
    async def toggle_registration(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        selected_tourneys = await prompt_tourneys_selector(
            inter, tourneys=await Tourney.filter(guild_id=inter.guild_id).order_by("id"), force_dropdown=True
        )
        if not selected_tourneys:
            return

    @discord.ui.button(label="Ban / Unban User(s)", style=discord.ButtonStyle.danger)
    async def ban_unban_user(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

    @discord.ui.button(label="Manage Groups", style=discord.ButtonStyle.secondary)
    async def manage_tourney_groups(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

    @discord.ui.button(label="Cancel Slots", style=discord.ButtonStyle.red)
    async def cancel_tourney_slots(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

    @discord.ui.button(label="Manually Add Slot(s)", style=discord.ButtonStyle.green)
    async def manually_add_tourney_slots(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Slot-Manager channel")
    async def tourney_slotmanager(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.green, label="Export Excel Sheet")
    async def download_excel_sheet(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()
