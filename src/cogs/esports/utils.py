import re
import discord, string
import humanize
import config
from utils.default import regional_indicator, keycap_digit
from utils import inputs, constants
from discord.ext import menus
from .errors import ScrimError
from datetime import datetime, timedelta
from utils import time
from models import Scrim, ArrayRemove, ArrayAppend
from discord.ext.menus import Button


class ScrimID:
    ...


async def check_if_correct_scrim(bot, scrim) -> bool:
    guild = scrim.guild
    registration_channel = scrim.registration_channel
    role = scrim.role
    _bool = True
    embed = discord.Embed(color=discord.Color.red())
    embed.description = f"Registration of `scrim {scrim.id}` couldn't be opened due to the following reason:\n"

    if not registration_channel:
        embed.description += (
            "I couldn't find registration channel. Maybe its deleted or hidden from me."
        )
        _bool = False

    elif not registration_channel.permissions_for(guild.me).manage_channels:
        embed.description += "I don't have permissions to manage {0}".format(
            registration_channel.mention
        )
        _bool = False

    elif scrim.role is None:
        embed.description += "I couldn't find success role."
        _bool = False

    elif (
        not guild.me.guild_permissions.manage_roles
        or role.position >= guild.me.top_role.position
    ):
        embed.description += "I don't have permissions to `manage roles` in this server or {0} is above my top role ({1}).".format(
            role.mention, guild.me.top_role.mention
        )
        _bool = False

    elif scrim.open_role_id and not scrim.open_role:
        embed.description += "You have set a custom open role which is deleted."
        _bool = False

    if not _bool:
        logschan = scrim.logschan
        if logschan and logschan.permissions_for(guild.me).send_messages:
            await logschan.send(
                content=getattr(scrim.modrole, "mention", None),
                embed=embed,
                allowed_mentions=discord.AllowedMentions(roles=True),
            )

    return _bool


async def postpone_scrim(bot, scrim):
    reminder = bot.get_cog("Reminders")

    await Scrim.filter(pk=scrim.id).update(
        open_time=scrim.open_time + timedelta(hours=24)
    )
    await scrim.refresh_from_db(("open_time",))

    await reminder.create_timer(
        scrim.open_time,
        "scrim_open",
        scrim_id=scrim.id,
    )


async def toggle_channel(channel, role, _bool=True):
    overwrite = channel.overwrites_for(role)
    overwrite.update(send_messages=_bool)
    try:
        await channel.set_permissions(
            role,
            overwrite=overwrite,
            reason=("Registration is over!", "Open for Registrations!")[
                _bool
            ],  # False=0, True=1
        )

        return True

    except:
        return False


async def scrim_end_process(ctx, scrim):
    opened_at = scrim.opened_at
    closed_at = datetime.now(tz=constants.IST)

    registration_channel = ctx.channel
    open_role = scrim.open_role

    await Scrim.filter(pk=scrim.id).update(
        opened_at=None, closed_at=datetime.now(tz=constants.IST)
    )

    channel_update = await toggle_channel(registration_channel, open_role, False)

    await ctx.send(
        embed=discord.Embed(
            color=config.COLOR, description="**Registration is now Closed!**"
        )
    )

    ctx.bot.dispatch("scrim_log", "closed", scrim, permission_updated=channel_update)

    if scrim.autoslotlist:
        time_taken = closed_at - opened_at
        delta = datetime.now() - timedelta(seconds=time_taken.total_seconds())

        time_taken = humanize.precisedelta(delta)

        embed, channel = await scrim.create_slotlist

        embed.set_footer(text="Registration took: {0}".format(time_taken))
        embed.color = config.COLOR

        if channel != None and channel.permissions_for(ctx.me).send_messages:
            await channel.send(embed=embed)


class DaysMenu(menus.Menu):
    def __init__(self, *, scrim: Scrim):
        super().__init__(
            timeout=60,
            delete_message_after=False,
            clear_reactions_after=True,
        )
        self.scrim = scrim
        self.days = scrim.open_days
        self.check = (
            lambda msg: msg.channel == self.ctx.channel
            and msg.author == self.ctx.author
        )

        # Adding buttons dynamically
        for idx, day in enumerate(constants.Day, start=1):

            def action(day):
                async def wraps(self, payload):
                    await self.update_scrim(day)

                return wraps

            self.add_button(Button(keycap_digit(idx), action(day)))

    def initial_embed(self):
        scrim = self.scrim
        embed = discord.Embed(color=discord.Color(config.COLOR))
        embed.title = "Edit Open Days: {0}".format(scrim.id)
        description = "\n".join(
            f"{idx:02}. {(day.value.title()).ljust(10)}   {('❌', '✅')[day in scrim.open_days]}"
            for idx, day in enumerate(constants.Day, start=1)
        )
        embed.description = f"```{description}```"
        return embed

    async def refresh(self):
        self.scrim = await Scrim.get(pk=self.scrim.id)
        await self.message.edit(embed=self.initial_embed())

    async def update_scrim(self, day):
        # Lets do some magic
        func = (ArrayAppend, ArrayRemove)[day in self.scrim.open_days]
        await Scrim.filter(pk=self.scrim.id).update(open_days=func("open_days", day))
        await self.refresh()

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.initial_embed())

    @menus.button("\N{BLACK SQUARE FOR STOP}\ufe0f")
    async def on_stop(self, payload):
        self.stop()


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
