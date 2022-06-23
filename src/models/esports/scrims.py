import asyncio
import io
from ast import literal_eval as leval
from contextlib import suppress
from datetime import timedelta
from pathlib import Path
from typing import List, Optional, Union

import discord
import humanize
from discord.ext.commands import (BadArgument, ChannelNotFound,
                                  TextChannelConverter)
from PIL import Image, ImageDraw, ImageFont
from tortoise import fields, models

import utils
from constants import AutocleanType, Day, EsportsLog, EsportsRole
from core import Context
from models import BaseDbModel
from models.helpers import *
from utils import discord_timestamp, plural, truncate_string


class Scrim(BaseDbModel):
    class Meta:
        table = "sm.scrims"

    id = fields.BigIntField(pk=True, index=True)
    guild_id = fields.BigIntField()
    name = fields.TextField(default="Quotient-Scrims")
    registration_channel_id = fields.BigIntField(index=True)
    slotlist_channel_id = fields.BigIntField()
    slotlist_message_id = fields.BigIntField(null=True)
    role_id = fields.BigIntField(null=True)
    required_mentions = fields.IntField(default=4)
    start_from = fields.IntField(default=1)
    available_slots = ArrayField(fields.IntField(), default=list)
    total_slots = fields.IntField()
    host_id = fields.BigIntField()
    open_time = fields.DatetimeField()
    opened_at = fields.DatetimeField(null=True)
    closed_at = fields.DatetimeField(null=True)

    autoclean = ArrayField(fields.CharEnumField(AutocleanType), default=lambda: list(AutocleanType))
    autoclean_done = fields.BooleanField(default=False)
    autoclean_time = fields.DatetimeField(null=True)

    autoslotlist = fields.BooleanField(default=True)
    ping_role_id = fields.BigIntField(null=True)
    multiregister = fields.BooleanField(default=False)
    stoggle = fields.BooleanField(default=True)
    open_role_id = fields.BigIntField(null=True)
    autodelete_rejects = fields.BooleanField(default=False)
    autodelete_extras = fields.BooleanField(default=True)
    teamname_compulsion = fields.BooleanField(default=False)

    time_elapsed = fields.CharField(null=True, max_length=100)
    show_time_elapsed = fields.BooleanField(default=True)

    open_days = ArrayField(fields.CharEnumField(Day), default=lambda: list(Day))
    slotlist_format = fields.TextField(null=True)

    no_duplicate_name = fields.BooleanField(default=False)

    open_message = fields.JSONField(default=dict)
    close_message = fields.JSONField(default=dict)
    banlog_channel_id = fields.BigIntField(null=True)

    match_time = fields.DatetimeField(null=True)

    emojis = fields.JSONField(default=dict)  #!new
    cdn = fields.JSONField(default={"status": False, "countdown": 3, "msg": {}})  #!new

    assigned_slots: fields.ManyToManyRelation["AssignedSlot"] = fields.ManyToManyField("models.AssignedSlot")
    reserved_slots: fields.ManyToManyRelation["ReservedSlot"] = fields.ManyToManyField("models.ReservedSlot")
    banned_teams: fields.ManyToManyRelation["BannedTeam"] = fields.ManyToManyField("models.BannedTeam")
    slot_reminders: fields.ManyToManyRelation["ScrimsSlotReminder"] = fields.ManyToManyField("models.ScrimsSlotReminder")

    def __str__(self):
        return f"{getattr(self.registration_channel,'mention','deleted-channel')} (ID: {self.id})"

    @classmethod
    async def convert(cls, ctx, argument: Union[str, discord.TextChannel]):
        scrim = None

        try:
            _c = await TextChannelConverter().convert(ctx, argument)
            scrim = await cls.get_or_none(registration_channel_id=_c.id, guild_id=ctx.guild.id)
        except ChannelNotFound:
            if argument.isdigit():
                scrim = await cls.get_or_none(pk=int(argument), guild_id=ctx.guild.id)

        if not scrim:
            raise BadArgument(
                f"This is not a valid Scrim ID or registration channel.\n\nGet a valid ID with `{ctx.prefix}s config`"
            )

        return scrim

    @property
    def guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def role(self):
        if self.guild is not None:
            return self.guild.get_role(self.role_id)

    @property
    def logschan(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.text_channels, name="quotient-scrims-logs")

    @property
    def modrole(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.roles, name="scrims-mod")

    @property
    def registration_channel(self):
        return self.bot.get_channel(self.registration_channel_id)

    @property
    def banlog_channel(self):
        return self.bot.get_channel(self.banlog_channel_id)

    @property
    def slotlist_channel(self):
        return self.bot.get_channel(self.slotlist_channel_id)

    @property
    def host(self):
        if self.guild is not None:
            return self.guild.get_member(self.host_id)

        return self.bot.get_user(self.host_id)

    @property
    def check_emoji(self):
        return self.emojis.get("tick", "✅")

    @property
    def cross_emoji(self):
        return self.emojis.get("cross", "❌")

    @property
    def available_to_reserve(self):
        """
        gives a range obj of available slots to reserve.
        this isn't true because some slots might be already reserved , we will sort them later
        """
        return range(self.start_from, self.total_slots + self.start_from)

    @property
    def opened(self):
        if self.opened_at is None:
            return False

        if self.closed_at is not None:
            return self.closed_at < self.opened_at

        return True

    @property
    def closed(self):
        return not self.opened

    @property
    def ping_role(self):
        if self.guild is not None:
            return self.guild.get_role(self.ping_role_id)

    @property
    def open_role(self):
        if self.guild is not None:
            if self.open_role_id is not None:
                return self.guild.get_role(self.open_role_id)
            return self.guild.default_role

    @property  # what? you think its useless , i know :)
    def toggle(self):
        return self.stoggle

    @property
    def teams_registered(self):  # This should be awaited
        return self.assigned_slots.order_by("num")

    async def reserved_user_ids(self):
        return (i.user_id for i in await self.reserved_slots.all())

    async def banned_user_ids(self):
        return (i.user_id for i in await self.banned_teams.all())

    async def cleaned_slots(self) -> List["AssignedSlot"]:
        slots = await self.assigned_slots.order_by("num")

        _list = []
        for _ in {slot.num for slot in slots}:
            _list.append(next(i for i in slots if i.num == _))

        return _list

    async def create_slotlist(self):

        _slots = await self.cleaned_slots()

        desc = "\n".join(f"Slot {slot.num:02}  ->  {slot.team_name}" for slot in _slots)

        if self.slotlist_format is not None:
            format = leval(self.slotlist_format)

            embed = discord.Embed.from_dict(format)

            description = embed.description.replace("\n" * 3, "") if embed.description else ""

            embed.description = f"""
            ```\n{desc}\n```
            {description}
            """

        else:
            embed = discord.Embed(title=self.name + " Slotlist", description=f"```\n{desc}\n```", color=self.bot.color)

        if self.show_time_elapsed and self.time_elapsed:
            embed.set_footer(text=f"Registration took: {self.time_elapsed}")

        if embed.color == discord.Embed.Empty:
            embed.color = 0x2F3136

        channel = self.slotlist_channel
        return embed, channel

    async def refresh_slotlist_message(self, msg: discord.Message = None):
        embed, channel = await self.create_slotlist()

        with suppress(discord.HTTPException, AttributeError):
            if not msg:
                msg = await self.bot.get_or_fetch_message(channel, self.slotlist_message_id)
                # msg = await channel.fetch_message(self.slotlist_message_id)

            await msg.edit(embed=embed)

    async def send_slotlist(self, channel: discord.TextChannel = None) -> discord.Message:
        from cogs.esports.views.smslotlist.button import SlotlistEditButton

        channel = channel or self.slotlist_channel

        _v = SlotlistEditButton(self.bot, self)
        embed, schannel = await self.create_slotlist()
        _v.message = await channel.send(embed=embed, view=_v)

        if channel == schannel:
            await self.make_changes(slotlist_message_id=_v.message.id)

        return _v.message

    async def dispatch_reminders(self, slot: "AssignedSlot", channel: discord.TextChannel, link: str):
        async for reminder in self.slot_reminders.all():
            user = self.bot.get_user(reminder.user_id)

            with suppress(discord.HTTPException, AttributeError):
                _e = discord.Embed(color=0x00FFB3, title=f"Slot Available to Claim - {channel.guild.name}", url=link)
                _e.description = (
                    f"A slot of {self} is available to claim in {channel.mention}!" "\nClaim it before anyone else do."
                )

                await user.send(embed=_e)

            await ScrimsSlotReminder.filter(pk=reminder.pk).delete()

    async def ensure_match_timer(self):

        from models import Timer

        from .slotm import ScrimsSlotManager

        if not self.match_time:
            self.match_time = self.bot.current_time.replace(hour=0, minute=0, microsecond=0, second=0)

        _time = self.match_time
        while _time < self.bot.current_time:
            _time = _time + timedelta(hours=24)

        if self.match_time != _time:
            await Scrim.filter(pk=self.pk).update(match_time=_time)

        check = await Timer.filter(
            event="scrim_match", expires=_time, extra={"args": [], "kwargs": {"scrim_id": self.pk}}
        ).exists()
        if not check:
            await self.bot.reminders.create_timer(_time, "scrim_match", scrim_id=self.pk)

        slotm = await ScrimsSlotManager.filter(scrim_ids__contains=self.pk).first()
        if slotm:
            await slotm.refresh_public_message()

    async def make_changes(self, **kwargs):
        await Scrim.filter(pk=self.pk).update(**kwargs)
        return await self.refresh_from_db()

    async def get_text_slotlist(self):
        _text = f"{self} Slot details:\n\n"
        _slots = await self.cleaned_slots()

        for _ in _slots:
            _text += f"{_.num}. {_.team_name} <@{_.user_id}>\n"

        return _text

    async def ban_slot(self, slot: "AssignedSlot", *, reason, mod: discord.Member, ban_type: str):
        to_ban, scrims = [slot.user_id], [self]

        if ban_type == "2":
            to_ban = [_ for _ in slot.members]

        elif ban_type == "3":
            scrims = await Scrim.filter(guild_id=self.guild_id).order_by("open_time")

        elif ban_type == "4":
            to_ban = [_ for _ in slot.members]
            scrims = await Scrim.filter(guild_id=self.guild_id).order_by("open_time")

        for _ in to_ban:
            for scrim in scrims:
                if _ in await scrim.banned_user_ids():
                    continue

                b = await BannedTeam.create(user_id=_, expires=reason.dt, reason=reason.arg)
                await scrim.banned_teams.add(b)

            if banlog := await BanLog.get_or_none(guild_id=self.guild_id):
                await banlog.log_ban(_, mod, scrims, reason)

            if reason.dt:
                await self.bot.reminders.create_timer(
                    reason.dt,
                    "scrim_ban",
                    scrims=[scrim.id for scrim in scrims],
                    user_id=_,
                    mod=mod.id,
                    reason=reason.arg,
                )

        return f"Banned {utils.plural(to_ban):player|players} from {utils.plural(scrims):scrim|scrims}."

    async def create_slotlist_img(self):
        """
        This is done! Now do whatever you can : )
        """
        slots = await self.teams_registered

        def wrapper():
            font = ImageFont.truetype(str(Path.cwd() / "src" / "data" / "font" / "Ubuntu-Regular.ttf"), 16)
            rects = []

            for slot in slots:
                image = Image.new("RGBA", (290, 30), "#2e2e2e")
                draw = ImageDraw.Draw(image)
                draw.text((10, 5), f"Slot {slot.num:02}  |  {slot.team_name}", font=font, fill="white")
                rects.append(image)

            # We will add 10 slots in a image.
            images = []
            for group in utils.split_list(rects, 10):
                size = (
                    290,
                    len(group) * 40,
                )
                image = Image.new("RGBA", size)
                x = 0
                y = 0

                for rect in group:
                    image.paste(rect, (x, y))
                    y += rect.size[1] + 10

                img_bytes = io.BytesIO()
                image.save(img_bytes, "PNG")
                img_bytes.seek(0)
                images.append(discord.File(img_bytes, "slotlist.png"))

            return images

        return await asyncio.get_event_loop().run_in_executor(
            None, wrapper
        )  # As pillow is blocking, we will process image in executor

    async def reg_open_msg(self):
        reserved_count = await self.reserved_slots.all().count()

        if len(self.open_message) <= 1:
            return discord.Embed(
                color=self.bot.color,
                title="Registration is now open!",
                description=f"📣 **`{self.required_mentions}`** mentions required.\n"
                f"📣 Total slots: **`{self.total_slots}`** [`{reserved_count}` slots reserved]",
            )

        changes = [
            ("<<mentions>>", str(self.required_mentions)),
            ("<<slots>>", str(self.total_slots)),
            ("<<reserved>>", str(reserved_count)),
            ("<<slotlist>>", getattr(self.slotlist_channel, "mention", "Not Found")),
            ("<<multireg>>", "Enabled" if self.multiregister else "Not Enabled"),
            ("<<teamname>>", "Yes" if self.teamname_compulsion else "No"),
            (
                "<<mention_banned>>",
                ", ".join(
                    map(lambda x: getattr(x, "mention", "Left"), map(self.guild.get_member, await self.banned_user_ids()))
                ),
            ),
            (
                "<<mention_reserved>>",
                ", ".join(
                    map(
                        lambda x: getattr(x, "mention", "Left"),
                        map(self.guild.get_member, await self.reserved_user_ids()),
                    )
                ),
            ),
        ]

        text = str(self.open_message)
        for _ in changes:
            text = text.replace(*_)

        return discord.Embed.from_dict(leval(text))

    def reg_close_msg(self):
        if len(self.close_message) <= 1:
            return discord.Embed(color=self.bot.config.COLOR, description="**Registration is now Closed!**")

        changes = [
            ("<<slots>>", str(self.total_slots)),
            ("<<filled>>", str(self.total_slots - len(self.available_slots))),
            ("<<time_taken>>", self.time_elapsed or "N/A"),
            ("<<open_time>>", discord_timestamp(self.open_time)),
        ]

        text = str(self.close_message)
        for _ in changes:
            text = text.replace(*_)

        return discord.Embed.from_dict(leval(text))

    async def setup_logs(self):
        _reason = "Created for scrims management."

        guild = self.guild

        if not (scrims_mod := self.modrole):
            scrims_mod = await guild.create_role(name="scrims-mod", color=self.bot.color, reason=_reason)

        overwrite = self.registration_channel.overwrites_for(guild.default_role)
        overwrite.update(read_messages=True, send_messages=True, read_message_history=True)
        await self.registration_channel.set_permissions(scrims_mod, overwrite=overwrite)

        if (scrims_log_channel := self.logschan) is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                scrims_mod: discord.PermissionOverwrite(read_messages=True),
            }
            scrims_log_channel = await guild.create_text_channel(
                name="quotient-scrims-logs",
                overwrites=overwrites,
                reason=_reason,
                topic="**DO NOT RENAME THIS CHANNEL**",
            )

            note = await scrims_log_channel.send(
                embed=discord.Embed(
                    description=f"If events related to scrims i.e opening registrations or adding roles, "
                    f"etc are triggered, then they will be logged in this channel. "
                    f"Also I have created {scrims_mod.mention}, you can give that role to your "
                    f"scrims-moderators. User with {scrims_mod.mention} can also send messages in "
                    f"registration channels and they won't be considered as scrims-registration.\n\n"
                    f"`Note`: **Do not rename this channel.**",
                    color=0x00FFB3,
                )
            )
            await note.pin()

    async def full_delete(self):
        from .slotm import ScrimsSlotManager

        _id = self.pk
        self.bot.cache.scrim_channels.discard(self.registration_channel.id)

        slotm = await ScrimsSlotManager.filter(scrim_ids__contains=self.pk)
        await ScrimsSlotManager.filter(pk__in=[_.pk for _ in slotm]).update(scrim_ids=ArrayRemove("scrim_ids", _id))

        _d = await self.assigned_slots.all()
        await AssignedSlot.filter(pk__in=[_.pk for _ in _d]).delete()
        _r = await self.slot_reminders.all()
        await ScrimsSlotReminder.filter(pk__in=[_.pk for _ in _r]).delete()
        _re = await self.reserved_slots.all()
        await ReservedSlot.filter(pk__in=[_.pk for _ in _re]).delete()
        await self.delete()

    async def confirm_all_scrims(self, ctx: Context, **kwargs):
        prompt = await ctx.prompt("Do you want to apply these changes to all scrims in this server?")
        if not prompt:
            return await ctx.simple("Alright, this scrim only.", 4)

        await Scrim.filter(guild_id=ctx.guild.id).update(**kwargs)
        await ctx.simple("This change was applied to all your scrims.", 4)

    async def close_registration(self):
        from cogs.esports.helpers.utils import toggle_channel, wait_and_purge

        from .slotm import ScrimsSlotManager

        closed_at = self.bot.current_time
        registration_channel = self.registration_channel
        open_role = self.open_role

        self.time_elapsed = humanize.precisedelta(closed_at - self.opened_at)
        await self.make_changes(opened_at=None, time_elapsed=self.time_elapsed, closed_at=closed_at)

        channel_update = await toggle_channel(registration_channel, open_role, False)
        _e = self.reg_close_msg()
        await registration_channel.send(embed=_e)

        self.bot.dispatch("scrim_log", EsportsLog.closed, self, permission_updated=channel_update)

        registered = await self.teams_registered

        if self.autoslotlist and registered:
            await self.send_slotlist()

        if self.autodelete_extras:
            msg_ids = (i.message_id for i in registered)

            check = lambda x: all(
                (not x.pinned, not x.reactions, not x.embeds, not x.author == self.bot.user, not x.id in msg_ids)
            )
            self.bot.loop.create_task(wait_and_purge(registration_channel, check=check, wait_for=20))

        slotm = await ScrimsSlotManager.get_or_none(scrim_ids__contains=self.id)
        if slotm:
            await slotm.refresh_public_message()

    async def start_registration(self):
        from cogs.esports.helpers.utils import (available_to_reserve,
                                                scrim_work_role,
                                                toggle_channel)

        oldslots = await self.assigned_slots
        await AssignedSlot.filter(id__in=(slot.id for slot in oldslots)).delete()
        await self.assigned_slots.clear()

        # here we insert a list of slots we can give for the registration.
        await self.bot.db.execute(
            """
            UPDATE public."sm.scrims" SET available_slots = $1 WHERE id = $2
            """,
            await available_to_reserve(self),
            self.id,
        )

        scrim_role = self.role

        async for slot in self.reserved_slots.all():
            assinged_slot = await AssignedSlot.create(
                num=slot.num,
                user_id=slot.user_id,
                team_name=slot.team_name,
                jump_url=None,
            )

            await self.assigned_slots.add(assinged_slot)

            if slot.user_id:
                with suppress(AttributeError):
                    self.bot.loop.create_task(self.guild.get_member(slot.user_id).add_roles(scrim_role))

        await Scrim.filter(pk=self.id).update(
            opened_at=self.bot.current_time,
            closed_at=None,
            slotlist_message_id=None,
        )
        self.bot.loop.create_task(self.ensure_match_timer())
        await asyncio.sleep(0.2)

        # Opening Channel for Normal Janta
        registration_channel = self.registration_channel
        open_role = self.open_role

        _e = await self.reg_open_msg()

        await registration_channel.send(
            content=scrim_work_role(self, EsportsRole.ping),
            embed=_e,
            allowed_mentions=discord.AllowedMentions(roles=True, everyone=True),
        )

        self.bot.cache.scrim_channels.add(registration_channel.id)

        await toggle_channel(registration_channel, open_role, True)
        self.bot.dispatch("scrim_log", EsportsLog.open, self)

    @staticmethod
    async def show_selector(*args, **kwargs):
        """
        :param: ctx: Context
        :param: scrims: List[Scrim]
        :param: placeholder:str
        :param: multi:bool=True
        """
        from cogs.esports.views.scrims.selector import prompt_selector

        return await prompt_selector(*args, **kwargs)

    async def scrim_posi(self):
        from cogs.esports.views.scrims.selector import scrim_position

        return await scrim_position(self.pk, self.guild_id)


class BaseSlot(models.Model):
    class Meta:
        abstract = True

    id = fields.IntField(pk=True)
    num = fields.IntField(null=True)  # this will never be null but there are already records in the table so
    user_id = fields.BigIntField(null=True)
    team_name = fields.TextField(null=True)
    members = ArrayField(fields.BigIntField(), default=list)


class AssignedSlot(BaseSlot):
    class Meta:
        table = "sm.assigned_slots"

    message_id = fields.BigIntField(null=True)
    jump_url = fields.TextField(null=True)


class ReservedSlot(BaseSlot):
    class Meta:
        table = "sm.reserved_slots"

    expires = fields.DatetimeField(null=True)

    @property
    def leader(self):
        return self.bot.get_user(self.user_id)


class BannedTeam(BaseSlot):
    class Meta:
        table = "sm.banned_teams"

    reason = fields.CharField(max_length=200, null=True)
    expires = fields.DatetimeField(null=True)


class BanLog(BaseDbModel):
    class Meta:
        table = "esports_bans"

    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField()
    channel_id = fields.BigIntField()

    @property
    def channel(self):
        return self.bot.get_channel(self.channel_id)

    def __format_scrims(self, scrims: List[Scrim]):

        _scrims = []
        for idx, _ in enumerate(scrims, start=1):
            if idx < 4:
                _scrims.append(getattr(_.registration_channel, "mention", "`deleted-channel`"))

            elif idx == 4:
                _scrims.append(f"**...{len(scrims) -  3} more**")

        return ", ".join(_scrims)

    async def log_ban(self, user_id: int, mod: discord.Member, scrims: List[Scrim], reason):

        user = await self.bot.getch(self.bot.get_user, self.bot.fetch_user, user_id)

        _e = discord.Embed(color=discord.Color.red(), title=f"🔨 Banned from {plural(scrims):scrim|scrims}")
        _e.add_field(name="User", value=f"{user} ({getattr(user, 'mention','unknown-user')})")
        _e.add_field(name="Moderator", value=mod)
        _e.add_field(name="Effected Scrims", value=self.__format_scrims(scrims), inline=False)
        _e.add_field(name="Reason", value=f"```{truncate_string(reason.arg,100) if reason.arg else 'No reason given'}```")

        _e.set_footer(text=f"Expiring: {'Never' if not reason.dt else ''}")
        if reason.dt:
            _e.timestamp = reason.dt

        if user:
            _e.set_thumbnail(url=getattr(user.display_avatar, "url", "https://cdn.discordapp.com/embed/avatars/0.png"))

        with suppress(discord.HTTPException, AttributeError):
            await self.channel.send(getattr(user, "mention", ""), embed=_e)

    async def log_unban(self, user_id: int, mod: discord.Member, scrims: List[Scrim], reason: str = None):

        user = await self.bot.getch(self.bot.get_user, self.bot.fetch_user, user_id)
        _e = discord.Embed(color=discord.Color.green(), title=f"🍃 Unbanned from {plural(scrims):Scrim|Scrims}")
        _e.add_field(name="User", value=f"{user} ({getattr(user, 'mention','unknown-user')})")
        _e.add_field(name="Moderator", value=mod)
        _e.add_field(name="Effected Scrims", value=self.__format_scrims(scrims), inline=False)
        _e.add_field(name="Reason", value=reason or "```No Reason given..```", inline=False)
        _e.timestamp = self.bot.current_time

        if user:
            _e.set_thumbnail(url=getattr(user.display_avatar, "url", "https://cdn.discordapp.com/embed/avatars/0.png"))

        with suppress(discord.HTTPException, AttributeError):
            await self.channel.send(getattr(user, "mention", ""), embed=_e)


class ScrimsSlotReminder(BaseDbModel):
    class Meta:
        table = "scrims_slot_reminders"

    id = fields.IntField(pk=True)
    user_id = fields.BigIntField()
    created_at = fields.DatetimeField(auto_now=True)
