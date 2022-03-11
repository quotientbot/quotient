from contextlib import suppress
import io
from tortoise import fields, exceptions
from discord.ext.commands import BadArgument

from typing import Optional, List, Union
from models.helpers import *

from models import BaseDbModel

from utils import split_list

import discord

_dict = {
    "tick": "✅",
    "cross": "❌",
}

from core import Context
from constants import EsportsLog


class Tourney(BaseDbModel):
    class Meta:
        table = "tm.tourney"

    id = fields.BigIntField(pk=True, index=True)
    guild_id = fields.BigIntField()
    name = fields.CharField(max_length=30, default="Quotient-Tourney")
    registration_channel_id = fields.BigIntField(index=True)
    confirm_channel_id = fields.BigIntField()
    role_id = fields.BigIntField()
    required_mentions = fields.SmallIntField(default=4, validators=[ValueRangeValidator(range(0, 11))])
    total_slots = fields.SmallIntField(validators=[ValueRangeValidator(range(1, 10001))])
    banned_users = ArrayField(fields.BigIntField(), default=list)
    host_id = fields.BigIntField()
    multiregister = fields.BooleanField(default=False)
    started_at = fields.DatetimeField(null=True)
    closed_at = fields.DatetimeField(null=True)
    open_role_id = fields.BigIntField(null=True)
    teamname_compulsion = fields.BooleanField(default=False)

    ping_role_id = fields.BigIntField(null=True)
    no_duplicate_name = fields.BooleanField(default=True)
    autodelete_rejected = fields.BooleanField(default=False)

    slotlist_start = fields.IntField(default=2)
    group_size = fields.IntField(null=True)

    success_message = fields.CharField(max_length=500, null=True)

    emojis = fields.JSONField(default=_dict)

    slotm_channel_id = fields.BigIntField(null=True)
    slotm_message_id = fields.BigIntField(null=True)

    assigned_slots: fields.ManyToManyRelation["TMSlot"] = fields.ManyToManyField("models.TMSlot")
    media_partners: fields.ManyToManyRelation["MediaPartner"] = fields.ManyToManyField("models.MediaPartner")

    def __str__(self):
        return f"{getattr(self.registration_channel,'mention','deleted-channel')} (Tourney: {self.id})"

    @classmethod
    async def convert(cls, ctx, argument: str):
        try:
            argument = int(argument)
        except ValueError:
            pass
        else:
            try:
                return await cls.get(pk=argument, guild_id=ctx.guild.id)
            except exceptions.DoesNotExist:
                pass

        raise BadArgument(f"This is not a valid Tourney ID.\n\nGet a valid ID with `{ctx.prefix}tourney config`")

    @property
    def guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def logschan(self) -> Optional[discord.TextChannel]:
        if (g := self.guild) is not None:
            return discord.utils.get(g.text_channels, name="quotient-tourney-logs")

    @property
    def registration_channel(self) -> Optional[discord.TextChannel]:
        if (g := self.guild) is not None:
            return g.get_channel(self.registration_channel_id)

    @property
    def confirm_channel(self) -> Optional[discord.TextChannel]:
        if (g := self.guild) is not None:
            return g.get_channel(self.confirm_channel_id)

    @property
    def slotm_channel(self) -> Optional[discord.TextChannel]:
        if (g := self.guild) is not None:
            return g.get_channel(self.slotm_channel_id)

    @property
    def closed(self):
        return bool(self.closed_at)

    @property
    def role(self) -> Optional[discord.Role]:
        if (g := self.guild) is not None:
            return g.get_role(self.role_id)

    @property
    def open_role(self):
        if (g := self.guild) is not None:
            if self.open_role_id is not None:
                return g.get_role(self.open_role_id)
            return self.guild.default_role

    @property
    def ping_role(self):
        if (g := self.guild) is not None:
            if self.ping_role_id is not None:
                return g.get_role(self.ping_role_id)
            return None

    @property
    def modrole(self):
        if (g := self.guild) is not None:
            return discord.utils.get(g.roles, name="tourney-mod")

    @property
    def check_emoji(self):
        return self.emojis.get("tick", "✅")

    @property
    def cross_emoji(self):
        return self.emojis.get("cross", "❌")

    @staticmethod
    def is_ignorable(member: discord.Member) -> bool:
        return "tourney-mod" in (role.name.lower() for role in member.roles)

    async def get_groups(self) -> List[List["TMSlot"]]:
        return split_list(await self.assigned_slots.all().order_by("num"), self.group_size)

    async def get_group(self, num: int) -> List["TMSlot"]:

        _all = await self.get_groups()
        for group in _all:
            if _all.index(group) == num - 1:
                return group

    async def get_group(self, num: int, size: int) -> Union[List["TMSlot"], None]:
        _list = await self.get_groups(size)
        for _chunk in _list:
            if _list.index(_chunk) == num - 1:
                return _chunk

    async def add_assigned_slot(self, slot: "TMSlot", message: discord.Message):
        _e = discord.Embed(color=self.bot.color)
        _e.description = f"**{slot.num}) NAME: [{slot.team_name.upper()}]({slot.jump_url})**\n"

        if len(message.mentions) > 0:
            _e.description += f"Team: {', '.join([str(m) for m in message.mentions])}"

        if _chan := self.confirm_channel:
            m = await _chan.send(
                content=message.author.mention, embed=_e, allowed_mentions=discord.AllowedMentions(users=True)
            )

            slot.confirm_jump_url = m.jump_url

            await slot.save()
            await self.assigned_slots.add(slot)

    async def finalize_slot(self, ctx: Context):
        """
        Add role to user and reaction to the message
        """
        with suppress(discord.HTTPException):

            if not (_role := self.role) in ctx.author.roles:
                await ctx.author.add_roles(_role)

            await ctx.message.add_reaction(self.check_emoji)

            if self.success_message:
                embed = ctx.bot.embed(ctx, title="Tournament Registration Successful", description=self.success_message)
                await ctx.author.send(embed=embed)

    async def end_process(self):

        from cogs.esports.helpers.utils import toggle_channel

        closed_at = self.bot.current_time

        registration_channel = self.registration_channel
        open_role = self.open_role

        await Tourney.filter(pk=self.id).update(started_at=None, closed_at=closed_at)
        channel_update = await toggle_channel(registration_channel, open_role, False)
        await registration_channel.send(
            embed=discord.Embed(color=self.bot.color, description="**Registration is now closed!**")
        )

        self.bot.dispatch("tourney_log", EsportsLog.closed, self, permission_updated=channel_update)

    async def setup_slotm(self):
        from cogs.esports.views.tourney.slotm import TourneySlotManager

        _view = TourneySlotManager(self.bot, tourney=self)
        _category = self.registration_channel.category
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(
                read_messages=True, send_messages=False, read_message_history=True
            ),
            self.guild.me: discord.PermissionOverwrite(manage_channels=True, manage_permissions=True),
        }
        slotm_channel = await _category.create_text_channel(name="tourney-slotmanager", overwrites=overwrites)
        return await slotm_channel.send(embed=TourneySlotManager.initial_embed(self), view=_view)

    async def get_csv(self):
        guild = self.guild
        member_ids = [_.id for _ in guild.members]

        _x = "Reg Posi,Team Name,Leader,Leader ID,Teammates,Teammates in Server,Jump URL\n"

        async for slot in self.assigned_slots.all().order_by("num"):
            _team = " | ".join((f"{str(guild.get_member(m))} ({m})" for m in slot.members))

            _x += (
                f"{slot.num},{slot.team_name},{str(guild.get_member(slot.leader_id))},"
                f"'{slot.leader_id}',{_team},{sum(1 for i in slot.members if i in member_ids)},{slot.jump_url}\n"
            )

        fp = io.BytesIO(_x.encode())

        return discord.File(fp, filename=f"tourney_data_{self.id}_{self.bot.current_time.timestamp()}.csv")

    async def full_delete(self) -> None:
        self.bot.cache.tourney_channels.discard(self.registration_channel_id)
        _data = await self.assigned_slots.all()
        await TMSlot.filter(pk__in=[_.id for _ in _data]).delete()
        await self.delete()

        if self.slotm_channel_id:
            with suppress(discord.HTTPException, AttributeError):
                await self.slotm_channel.delete()

    @staticmethod
    async def prompt_selector(ctx: Context, *, tourneys: List["Tourney"] = None, placeholder: str = None):

        placeholder = placeholder or "Choose a tourney to contine..."

        from cogs.esports.views.tourney._select import TourneySelector, QuotientView

        tourneys = tourneys or await Tourney.filter(guild_id=ctx.guild.id).order_by("id").limit(25)

        if not tourneys:
            return None

        view = QuotientView(ctx)
        view.add_item(TourneySelector(placeholder, tourneys))

        view.message = await ctx.send("Choose a tourney from the dropdown below...", view=view)
        await view.wait()
        if view.custom_id:
            await view.message.delete()
            return await Tourney.get_or_none(id=view.custom_id)

    async def setup_logs(self):
        _reason = "Created for tournament management."
        _g = self.guild

        if not (tourney_mod := self.modrole):
            tourney_mod = await self.guild.create_role(name="tourney-mod", color=self.bot.color, reason=_reason)

        overwrite = self.registration_channel.overwrites_for(_g.default_role)
        overwrite.update(read_messages=True, send_messages=True, read_message_history=True)
        await self.registration_channel.set_permissions(tourney_mod, overwrite=overwrite)

        if (tourney_log_channel := self.logschan) is None:
            overwrites = {
                _g.default_role: discord.PermissionOverwrite(read_messages=False),
                _g.me: discord.PermissionOverwrite(read_messages=True),
                tourney_mod: discord.PermissionOverwrite(read_messages=True),
            }
            tourney_log_channel = await _g.create_text_channel(
                name="quotient-tourney-logs",
                overwrites=overwrites,
                reason=_reason,
                topic="**DO NOT RENAME THIS CHANNEL**",
            )

            note = await tourney_log_channel.send(
                embed=discord.Embed(
                    description=f"If events related to tournament i.e opening registrations or adding roles, "
                    f"etc are triggered, then they will be logged in this channel. "
                    f"Also I have created {tourney_mod.mention}, you can give that role to your "
                    f"tourney-moderators. User with {tourney_mod.mention} can also send messages in "
                    f"registration channels and they won't be considered as tourney-registration.\n\n"
                    f"`Note`: **Do not rename this channel.**",
                    color=discord.Color(self.bot.color),
                )
            )
            await note.pin()

    async def toggle_registrations(self):
        channel, open_role = self.registration_channel, self.open_role
        if not channel:
            return False, f"I cannot find the registration channel. ({self.registration_channel_id})"

        if not channel.permissions_for(self.guild.me).manage_permissions:
            return False, f"I don't have permission to manage channel permissions. ({channel.id})"

        if not open_role:
            return False, f"I cannot find the open role. ({self.open_role_id})"

        if self.started_at:
            return await self.__stop_registrations()

        return await self.__start_registrations()

    async def __start_registrations(self):
        registration_channel = self.registration_channel

        if self.total_slots <= await self.assigned_slots.all().count():
            return False, "Slots are already full, Increase slots to start again."

        await Tourney.filter(pk=self.id).update(started_at=self.bot.current_time, closed_at=None)
        self.bot.cache.tourney_channels.add(self.registration_channel_id)

        _e = discord.Embed(color=self.bot.color, title=f"{self.name} Registration is Open")
        _e.description = (
            f"📣 **`{self.required_mentions}`** mentions required.\n"
            f"📣 Total slots: **`{self.total_slots}`** [`{self.total_slots - await self.assigned_slots.all().count()}` slots left]"
        )
        _e.set_thumbnail(url=self.bot.user.avatar.url)
        _ping = None
        if p := self.ping_role:
            if p == self.guild.default_role:
                _ping = "@everyone"

            else:
                _ping = p.mention

        await registration_channel.send(
            _ping, embed=_e, allowed_mentions=discord.AllowedMentions(roles=True, everyone=True)
        )
        await registration_channel.set_permissions(self.open_role, send_messages=True)
        return True, True

    async def __stop_registrations(self):
        registration_channel = self.registration_channel

        await registration_channel.set_permissions(self.open_role, send_messages=False)
        await registration_channel.send(
            embed=discord.Embed(color=self.bot.color, description=f"**{self.name} registration paused.**")
        )
        await Tourney.filter(pk=self.id).update(started_at=None, closed_at=self.bot.current_time)
        return True, True

    async def ban_user(self, user: Union[discord.Member, discord.User]):
        await Tourney.filter(pk=self.id).update(banned_users=ArrayAppend("banned_users", user.id))

    async def unban_user(self, user: Union[discord.Member, discord.User]):
        await Tourney.filter(pk=self.id).update(banned_users=ArrayRemove("banned_users", user.id))

    async def remove_slot(self, slot: "TMSlot"):
        if slot.confirm_jump_url:
            self.bot.loop.create_task(self.update_confirmed_message(slot.confirm_jump_url))

        await slot.delete()

        if not await self.assigned_slots.filter(leader_id=slot.leader_id).exists():
            m = self.guild.get_member(slot.leader_id)
            if m:
                await m.remove_roles(discord.Object(id=self.role_id))

    async def update_confirmed_message(self, link: str):
        _ids = [int(i) for i in link.split("/")[5:]]

        with suppress(discord.HTTPException, IndexError):
            message = await self.guild.get_channel(_ids[0]).fetch_message(_ids[1])

            if message:
                e = message.embeds[0]

                e.description = "~~" + e.description.strip() + "~~"
                e.title = "Cancelled Slot"
                e.color = discord.Color.red()

                await message.edit(embed=e)

    async def make_changes(self, **kwargs):
        return await Tourney.filter(pk=self.id).update(**kwargs)

    async def refresh_slotlm(self):
        from cogs.esports.views.tourney import TourneySlotManager

        msg = await self.bot.get_or_fetch_message(self.slotm_channel, self.slotm_message_id)
        _view = TourneySlotManager(self.bot, tourney=self)
        _e = TourneySlotManager.initial_embed(self)

        try:
            await msg.edit(embed=_e, view=_view)
        except discord.HTTPException:
            msg = await self.slotm_channel.send(embed=_e, view=_view)
            await self.make_changes(slotm_message_id=msg.id)

        finally:
            return True


class TMSlot(BaseDbModel):
    class Meta:
        table = "tm.register"

    id = fields.BigIntField(pk=True)
    num = fields.IntField()
    team_name = fields.TextField()
    leader_id = fields.BigIntField()
    message_id = fields.BigIntField(null=True)
    members = ArrayField(fields.BigIntField(), default=list)
    confirm_jump_url = fields.CharField(max_length=300, null=True)
    jump_url = fields.TextField(null=True)


class MediaPartner(BaseDbModel):
    class Meta:
        table = "tm.media_partners"

    channel_id = fields.BigIntField(pk=True, generated=False)
    tourney_id = fields.IntField()
    slots: fields.ManyToManyRelation["PartnerSlot"] = fields.ManyToManyField("models.PartnerSlot")

    @property
    def channel(self) -> Optional[discord.TextChannel]:
        return self.bot.get_channel(self.channel_id)


class PartnerSlot(BaseDbModel):
    class Meta:
        table = "tm.media_partner_users"

    id = fields.IntField(pk=True)
    user_id = fields.BigIntField()
    message_id = fields.BigIntField()
    jump_url = fields.CharField(max_length=300, null=True)
    members = ArrayField(fields.BigIntField(), default=list)


class TGroupList(BaseDbModel):
    class Meta:
        table = "tm.group_list"

    message_id = fields.BigIntField(pk=True)
    channel_id = fields.BigIntField()
    refresh_at = fields.DatetimeField(auto_now=True)

    @property
    def channel(self):
        return self.bot.get_channel(self.channel_id)

    @property
    def jump_url(self):
        if c := self.channel:
            return f"https://discord.com/channels/{c.guild.id}/{self.channel_id}/{self.pk}"
