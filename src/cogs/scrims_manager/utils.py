from utils.default import regional_indicator
from discord.ext import menus
from .errors import ScrimError
from utils.time import time
from models import Scrim
from utils import inputs
import discord, string
import config


async def toggle_channel(channel, role, bool=True):
    overwrite = channel.overwrites_for(role)
    overwrite.update(send_messages=bool)
    try:
        await channel.set_permissions(
            role,
            overwrite=overwrite,
            reason=f"{'Open for Registrations!' if bool is True else 'Registration is over!'} ",
        )

        return True

    except:
        return False


class ConfigEditMenu(menus.Menu):
    def __init__(self, *, scrim: Scrim):
        super().__init__(
            timeout=100,
            delete_message_after=False,
            clear_reactions_after=True,
        )
        self.scrim = scrim
        self.check = (
            lambda msg: msg.channel == self.ctx.channel
            and msg.author == self.ctx.author
        )

    def initial_embed(self):
        scrim = self.scrim
        slotlist_channel = getattr(
            scrim.slotlist_channel, "mention", "`Channel Deleted!`"
        )
        registration_channel = getattr(
            scrim.registration_channel, "mention", "`Channel Deleted!`"
        )
        scrim_role = getattr(scrim.role, "mention", "`Role Deleted!`")
        open_time = (scrim.open_time).strftime("%I:%M %p")

        ping_role = (
            getattr(scrim.ping_role, "mention", "`Role Deleted!`")
            if scrim.ping_role_id
            else "`Not Configured!`"
        )
        open_role = (
            getattr(scrim.open_role, "mention", "`Role Deleted!`")
            if scrim.open_role_id
            else self.ctx.guild.default_role.mention
        )

        embed = discord.Embed(color=discord.Color(config.COLOR))
        embed.title = f"Edit Scrims Configuration: {scrim.id}"

        fields = {
            "Name": f"`{scrim.name}`",
            "Registration Channel": registration_channel,
            "Slotlist Channel": slotlist_channel,
            "Role": scrim_role,
            "Mentions": f"`{scrim.required_mentions:,}`",
            "Slots": f"`{scrim.total_slots:,}`",
            "Open Time": f"`{open_time}`",
            "Auto-clean": ("`No!`", "`Yes!`")[scrim.autoclean],
            "Ping Role": ping_role,
            "Open Role": open_role,
        }

        for idx, (name, value) in enumerate(fields.items()):
            embed.add_field(
                name=f"{regional_indicator(string.ascii_uppercase[idx])} {name}:",
                value=value,
            )

        embed.set_thumbnail(url=self.bot.user.avatar_url)
        return embed

    async def cembed(self, description):
        return await self.ctx.send(
            embed=discord.Embed(
                color=discord.Color(config.COLOR),
                title=f"🛠️ Scrims Manager",
                description=description,
            )
        )

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.initial_embed())

    async def refresh(self):
        self.scrim = await Scrim.get(pk=self.scrim.id)
        await self.message.edit(embed=self.initial_embed())

    async def update_scrim(self, **kwargs):
        await Scrim.filter(pk=self.scrim.id).update(**kwargs)
        await self.refresh()

    @menus.button(regional_indicator("A"))
    async def change_scrim_name(self, payload):
        msg = await self.cembed(
            "What is the new name you want to give to these scrims?"
        )
        name = await inputs.string_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        if len(name) > 30:
            raise ScrimError("Scrims Name cannot exceed 30 characters.")
        elif len(name) < 5:
            raise ScrimError("The length of new name is too short.")

        await inputs.safe_delete(msg)
        await self.update_scrim(name=name)

    @menus.button(regional_indicator("B"))
    async def change_registration_channel(self, payload):
        msg = await self.cembed("Which is the new channel for registrations?")
        channel = await inputs.channel_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        await inputs.safe_delete(msg)
        await self.update_scrim(registration_channel_id=channel.id)

    @menus.button(regional_indicator("C"))
    async def change_slotlist_channel(self, payload):
        msg = await self.cembed("Which is the new channel for slotlists?")
        channel = await inputs.channel_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        await inputs.safe_delete(msg)
        await self.update_scrim(slotlist_channel_id=channel.id)

    @menus.button(regional_indicator("D"))
    async def change_scrim_role(self, payload):
        msg = await self.cembed("Which is the new role for correct registration?")
        role = await inputs.role_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        await inputs.safe_delete(msg)
        await self.update_scrim(role_id=role.id)

    @menus.button(regional_indicator("E"))
    async def change_required_mentions(self, payload):
        msg = await self.cembed(
            "How many mentions are required for successful registration?"
        )
        mentions = await inputs.integer_input(
            self.ctx,
            self.check,
            delete_after=True,
            limits=(0, 10),
        )
        await inputs.safe_delete(msg)
        await self.update_scrim(required_mentions=mentions)

    @menus.button(regional_indicator("F"))
    async def change_total_slots(self, payload):
        msg = await self.cembed("How many total slots are there?")
        slots = await inputs.integer_input(
            self.ctx,
            self.check,
            delete_after=True,
            limits=(1, 30),
        )
        await inputs.safe_delete(msg)
        await self.update_scrim(total_slots=slots)

    @menus.button(regional_indicator("G"))
    async def change_open_time(self, payload):
        msg = await self.cembed(
            "**At what time should I open registrations?**"
            "\n> Time must be in 24h and in this format **`hh:mm`**\n"
            "**Example: 14:00** - Registration will open at 2PM.\n\n"
            "**Currently Quotient works according to Indian Standard Time (UTC+05:30)**"
        )

        open_time = await inputs.time_input(self.ctx, self.check, delete_after=True)
        await inputs.safe_delete(msg)

        await self.bot.get_cog("Reminders").create_timer(
            open_time,
            "scrim_open",
            scrim_id=self.scrim.id,
        )

        await self.update_scrim(open_time=open_time)

    # @menus.button(regional_indicator("H"))
    # async def change_open_sunday(self, payload):
    #     await self.update_scrim(open_sunday=not self.scrim.open_sunday)

    @menus.button(regional_indicator("H"))
    async def change_cleanup(self, payload):
        await self.update_scrim(cleanup=not self.scrim.autoclean)

    @menus.button(regional_indicator("I"))
    async def change_ping_role(self, payload):
        msg = await self.cembed("Which role should I ping when I open registrations?")

        role = await inputs.role_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        await inputs.safe_delete(msg)
        await self.update_scrim(ping_role_id=role.id)

    @menus.button(regional_indicator("J"))
    async def change_open_role(self, payload):
        msg = await self.cembed("For which role should I open registrations?")

        role = await inputs.role_input(
            self.ctx,
            self.check,
            delete_after=True,
        )

        await inputs.safe_delete(msg)
        await self.update_scrim(open_role_id=role.id)

    @menus.button("\N{BLACK SQUARE FOR STOP}\ufe0f")
    async def on_stop(self, payload):
        self.stop()
