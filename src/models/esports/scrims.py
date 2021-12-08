from models import BaseDbModel

from tortoise import fields, models
from models.helpers import *

from constants import AutocleanType, Day
from PIL import Image, ImageFont, ImageDraw
from discord.ext.commands import BadArgument, TextChannelConverter, ChannelNotFound

from ast import literal_eval as leval
from typing import Optional, Union
from pathlib import Path

import discord
import asyncio
import utils
import io


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
    required_mentions = fields.IntField()
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
    autodelete_extras = fields.BooleanField(default=False)
    teamname_compulsion = fields.BooleanField(default=False)

    time_elapsed = fields.CharField(null=True, max_length=100)
    show_time_elapsed = fields.BooleanField(default=True)

    open_days = ArrayField(fields.CharEnumField(Day), default=lambda: list(Day))
    slotlist_format = fields.TextField(null=True)

    no_duplicate_name = fields.BooleanField(default=False)

    open_message = fields.JSONField(default=dict)
    close_message = fields.JSONField(default=dict)
    banlog_channel_id = fields.BigIntField(null=True)

    assigned_slots: fields.ManyToManyRelation["AssignedSlot"] = fields.ManyToManyField("models.AssignedSlot")
    reserved_slots: fields.ManyToManyRelation["ReservedSlot"] = fields.ManyToManyField("models.ReservedSlot")
    banned_teams: fields.ManyToManyRelation["BannedTeam"] = fields.ManyToManyField("models.BannedTeam")

    def __str__(self):
        return f"{getattr(self.registration_channel,'mention','deleted-channel')} (Scrim: {self.id})"

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
        return self.assigned_slots.order_by("num").all()

    async def reserved_user_ids(self):
        return (i.user_id for i in await self.reserved_slots.all())

    async def banned_user_ids(self):
        return (i.user_id for i in await self.banned_teams.all())

    async def create_slotlist(self):
        slots = await self.teams_registered
        ids = {slot.num for slot in slots}
        fslots = []
        for id in ids:
            fslots.append([slot for slot in slots if slot.num == id][0])

        desc = "\n".join(f"Slot {slot.num:02}  ->  {slot.team_name}" for slot in fslots)

        if self.slotlist_format is not None:
            format = leval(self.slotlist_format)

            embed = discord.Embed.from_dict(format)

            description = embed.description.replace("\n" * 3, "") if embed.description else ""

            embed.description = f"```{desc}```\n{description}"

        else:
            embed = discord.Embed(title=self.name + " Slotlist", description=f"```{desc}```", color=self.bot.color)

        if self.show_time_elapsed and self.time_elapsed:
            embed.set_footer(text=f"Registration took: {self.time_elapsed}")

        if embed.color == discord.Embed.Empty:
            embed.color = 0x2F3136

        channel = self.slotlist_channel
        return embed, channel

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


class BannedTeam(BaseSlot):
    class Meta:
        table = "sm.banned_teams"

    reason = fields.CharField(max_length=200, null=True)
    expires = fields.DatetimeField(null=True)


class BanLog(models.Model):
    class Meta:
        table = "esports_bans"

    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField()
    channel_id = fields.BigIntField()

    @property
    def channel(self):
        return self.bot.get_channel(self.channel_id)
