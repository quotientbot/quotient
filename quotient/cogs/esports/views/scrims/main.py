import discord
from cogs.premium import SCRIMS_LIMIT, RequirePremiumView
from discord.ext import commands
from lib import CROSS, TICK, truncate_string
from models import Guild, Scrim

from ..scrims import ScrimsView
from .create_scrim import CreateScrimView
from .edit import ScrimsEditPanel
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
            for _ in self.children[1:]:
                _.disabled = True

        return e

    @discord.ui.button(label="Create Scrim", style=discord.ButtonStyle.primary)
    async def create_new_scrim(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        guild = await Guild.get(pk=inter.guild_id)

        if not guild.is_premium:
            if await Scrim.filter(guild_id=guild.pk).count() >= SCRIMS_LIMIT:
                v = RequirePremiumView(
                    f"You have reached the maximum limit of '{SCRIMS_LIMIT} scrims', Upgrade to Quotient Pro to unlock unlimited scrims."
                )

                return await inter.followup.send(
                    embed=v.premium_embed,
                    view=v,
                )

        self.stop()

        v = CreateScrimView(self.ctx)
        v.message = await self.message.edit(content="", embed=v.initial_msg(), view=v)

    @discord.ui.button(label="Edit Settings", style=discord.ButtonStyle.secondary)
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

        v = ScrimsEditPanel(self.ctx, scrims[0], await Guild.get(pk=inter.guild_id))
        v.message = await self.message.edit(content="", embed=await v.initial_msg(), view=v)

    @discord.ui.button(label="Instant Start/Stop Reg", style=discord.ButtonStyle.secondary)
    async def instant_start_stop_reg(self, inter: discord.Interaction, btn: discord.ui.Button):
        pass

    @discord.ui.button(label="Manage Slot Reservations", style=discord.ButtonStyle.secondary)
    async def manage_slot_reservations(self, inter: discord.Interaction, btn: discord.ui.Button):
        pass

    @discord.ui.button(label="Ban/Unban Teams", style=discord.ButtonStyle.secondary)
    async def ban_unban_teams(self, inter: discord.Interaction, btn: discord.ui.Button):
        pass

    @discord.ui.button(label="Change Designs", style=discord.ButtonStyle.secondary)
    async def change_designs(self, inter: discord.Interaction, btn: discord.ui.Button):
        pass

    @discord.ui.button(label="Slotlist Settings", style=discord.ButtonStyle.secondary)
    async def slotlist_settings(self, inter: discord.Interaction, btn: discord.ui.Button):
        pass

    @discord.ui.button(label="Enable / Disable Scrims", style=discord.ButtonStyle.danger)
    async def enable_disable_scrims(self, inter: discord.Interaction, btn: discord.ui.Button):
        pass
