from ...views.base import EsportsBaseView
from core import Context
from models import Tourney

from ...helpers import tourney_work_role

from utils import regional_indicator as ri, inputs, truncate_string, emote

from constants import EsportsRole
from string import ascii_uppercase

import discord


class TourneyEditor(EsportsBaseView):
    def __init__(self, ctx: Context, *, tourney: Tourney):
        super().__init__(ctx, timeout=60, title="Tourney Editor")

        self.ctx = ctx
        self.tourney = tourney

    @staticmethod
    def initial_message(tourney: Tourney) -> discord.Embed:

        slotlist_channel = getattr(tourney.confirm_channel, "mention", "`channel-deleted`")
        registration_channel = getattr(tourney.registration_channel, "mention", "`channel-deleted`")
        tourney_role = getattr(tourney.role, "mention", "`role-deleted`")

        open_role = tourney_work_role(tourney, EsportsRole.open)
        ping_role = tourney_work_role(tourney, EsportsRole.ping)

        embed = discord.Embed(color=0x00FFB3, title=f"Tourney Editor (ID: {tourney.id})")

        fields = {
            "Name": f"`{tourney.name}`",
            "Registration Channel": registration_channel,
            "Confirm Channel": slotlist_channel,
            "Success Role": tourney_role,
            "Mentions": f"`{tourney.required_mentions}`",
            "Ping Role": f"`not-set`" if not ping_role else ping_role,
            "Slots": f"`{tourney.total_slots:,}`",
            "Open Role": open_role,
            "Multi Register": ("`No`", "`Yes`")[tourney.multiregister],
            "Team Name Compulsion": ("`No!`", "`Yes!`")[tourney.teamname_compulsion],
            "Duplicate Team Names": ("`Allowed!`", "`Not Allowed`")[tourney.no_duplicate_name],
            "Autodelete Rejected Reg": ("`No!`", "`Yes!`")[tourney.autodelete_rejected],
        }

        for idx, (name, value) in enumerate(fields.items()):
            embed.add_field(
                name=f"{ri(ascii_uppercase[idx])} {name}:",
                value=value,
            )

        return embed

    async def update_tourney(self, **kwargs):
        await Tourney.filter(pk=self.tourney.id).update(**kwargs)
        await self.__refresh_view()

    async def __refresh_view(self):
        await self.tourney.refresh_from_db()
        embed = self.initial_message(self.tourney)
        try:
            self.message = await self.message.edit(embed=embed, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_name", emoji=ri("a"), row=1)
    async def set_name(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        msg = await self.ask_embed(
            "What should be the new name of this tourney?\n\n" "`Please Keep this under 30 characters.`"
        )

        new_name = await inputs.string_input(self.ctx, self.check, delete_after=True)

        new_name = truncate_string(new_name.strip(), 30)

        await self.ctx.safe_delete(msg)

        await self.update_tourney(name=new_name)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_reg_channel", emoji=ri("b"), row=1)
    async def set_reg_channel(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        msg = await self.ask_embed(
            "Which channel do you want to use as registration channel.\n\n`Mention the channel or enter its ID.`"
        )

        channel = await inputs.channel_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(msg)

        perms = channel.permissions_for(self.ctx.me)

        if not all((perms.manage_messages, perms.add_reactions, perms.manage_channels)):
            return await self.error_embed(
                f"Please make sure I have `add_reactions` and `manage_messages` permission in {channel.mention}."
            )

        await self.update_tourney(registration_channel_id=channel.id)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_confirm_channel", emoji=ri("c"), row=1)
    async def set_confirm_channel(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        msg = await self.ask_embed(
            "Which channel do you want to use as confirmation channel.\n\n`Mention the channel or enter its ID.`"
        )

        channel = await inputs.channel_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(msg)

        perms = channel.permissions_for(self.ctx.me)

        if not all((perms.manage_messages, perms.add_reactions)):
            return await self.error_embed(
                f"Please make sure I have `add_reactions` and `manage_messages` permission in {channel.mention}."
            )

        await self.update_tourney(confirm_channel_id=channel.id)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_role", emoji=ri("d"), row=1)
    async def set_role(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        msg = await self.ask_embed(
            "Which role do you want me to give for successful registration?\n\n" "`Mention the role or Enter its ID.`"
        )
        role = await inputs.role_input(self.ctx, self.check, delete_after=True)

        await self.ctx.safe_delete(msg)

        if not self.ctx.me.guild_permissions.manage_roles:
            return await self.error_embed("Unfortunately I don't have `manage_roles` permission.")

        await self.update_tourney(role_id=role.id)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_mentions", emoji=ri("e"), row=1)
    async def set_mentions(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        msg = await self.ask_embed(
            "How many mentions are required for successful registration?\n\n" "`Enter a number between 0 or 10.`"
        )
        mentions = await inputs.integer_input(self.ctx, self.check, delete_after=True, limits=(0, 10))
        await self.ctx.safe_delete(msg)

        await self.update_tourney(required_mentions=mentions)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_ping", emoji=ri("f"), row=2)
    async def set_ping_role(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        msg = await self.ask_embed(
            "Which role do you want me to ping when registration opens?\n\n" "`Mention the role or Enter its ID.`"
        )
        role = await inputs.role_input(self.ctx, self.check, delete_after=True)

        await self.ctx.safe_delete(msg)

        await self.update_tourney(ping_role_id=role.id)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_slots", emoji=ri("g"), row=2)
    async def set_slots(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        msg = await self.ask_embed(
            "How many total slots do you want to set?\n\n" "`Total slots cannot be more than 10,000.`"
        )
        slots = await inputs.integer_input(self.ctx, self.check, delete_after=True, limits=(1, 10000))
        await self.ctx.safe_delete(msg)

        await self.update_tourney(total_slots=slots)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_open_role", emoji=ri("h"), row=2)
    async def set_open_role(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        msg = await self.ask_embed(
            "For which role do you want me to open registrations?\n\n" "`Mention the role or Enter its ID.`"
        )
        role = await inputs.role_input(self.ctx, self.check, delete_after=True)

        await self.ctx.safe_delete(msg)

        await self.update_tourney(open_role_id=role.id)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_multireg", emoji=ri("i"), row=2)
    async def set_multireg(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        await self.update_tourney(multiregister=not self.tourney.multiregister)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_name_compulsion", emoji=ri("j"), row=2)
    async def set_name_compulsion(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        await self.update_tourney(teamname_compulsion=not self.tourney.teamname_compulsion)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_name_duplicacy", emoji=ri("k"), row=3)
    async def set_duplicacy(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        await self.update_tourney(no_duplicate_name=not self.tourney.no_duplicate_name)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_delete_rejected", emoji=ri("l"), row=3)
    async def set_autodelete(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        await self.update_tourney(autodelete_rejected=not self.tourney.autodelete_rejected)

    @discord.ui.button(
        style=discord.ButtonStyle.green, custom_id="tourney_success_message", label="Success Message", row=3
    )
    async def success_message(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        m = await self.ask_embed(
            "What message do you want me to show for successful registration? This message will be sent to "
            "DM of players who register successfully.\n\n**Current Success Message:**"
            f"```{self.tourney.success_message if self.tourney.success_message else 'Not Set Yet.'}```"
            "\n`Kindly keep it under 350 characters. Enter none to remove it.`",
            image="https://cdn.discordapp.com/attachments/851846932593770496/900977642382163988/unknown.png",
        )

        msg = await inputs.string_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(m)

        msg = truncate_string(msg, 350)
        if msg.lower().strip() == "none":
            msg = None
            await self.ctx.success("Removed Success Message.", 3)

        elif msg.lower().strip() == "cancel":
            return

        if msg != None:
            await self.ctx.success("Success Message Updated.", 3)
        await self.update_tourney(success_message=msg)

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="tourney_stop_view", emoji=emote.trash, row=3)
    async def stop_view(self, button: discord.Button, interaction: discord.Interaction):
        await self.on_timeout()
