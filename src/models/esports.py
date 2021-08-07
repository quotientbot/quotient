import asyncio
import io

from .fields import *
import discord
import utils
from PIL import Image, ImageFont, ImageDraw
from typing import Optional
from tortoise import models, fields
from constants import AutocleanType, Day, SSStatus, SSType
from pathlib import Path
from .functions import *
from ast import literal_eval as leval

__all__ = (
    "Tourney",
    "TMSlot",
    "Scrim",
    "AssignedSlot",
    "ReservedSlot",
    "BannedTeam",
    "TagCheck",
    "EasyTag",
    "PointsInfo",
    "PointsTable",
    "SSVerify",
    "SSData",
    "SlotManager"
)


class Tourney(models.Model):
    class Meta:
        table = "tm.tourney"

    id = fields.BigIntField(pk=True, index=True)
    guild_id = fields.BigIntField()
    name = fields.CharField(max_length=200, default="Quotient-Tourney")
    registration_channel_id = fields.BigIntField(index=True)
    confirm_channel_id = fields.BigIntField()
    role_id = fields.BigIntField()
    required_mentions = fields.IntField()
    total_slots = fields.IntField()
    banned_users = ArrayField(fields.BigIntField(), default=list)
    host_id = fields.BigIntField()
    multiregister = fields.BooleanField(default=False)
    started_at = fields.DatetimeField(null=True)
    closed_at = fields.DatetimeField(null=True)
    open_role_id = fields.BigIntField(null=True)
    teamname_compulsion = fields.BooleanField(default=False)

    assigned_slots: fields.ManyToManyRelation["TMSlot"] = fields.ManyToManyField("models.TMSlot")

    @property
    def guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def logschan(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.text_channels, name="quotient-tourney-logs")

    @property
    def registration_channel(self):
        if self.guild is not None:
            return self.guild.get_channel(self.registration_channel_id)

    @property
    def confirm_channel(self):
        if self.guild is not None:
            return self.guild.get_channel(self.confirm_channel_id)

    @property
    def closed(self):
        return bool(self.closed_at)

    @property
    def role(self):
        if self.guild is not None:
            return self.guild.get_role(self.role_id)

    @property
    def open_role(self):
        if self.guild is not None:
            if self.open_role_id != None:
                return self.guild.get_role(self.open_role_id)
            else:
                return self.guild.default_role

    @property
    def modrole(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.roles, name="tourney-mod")


class TMSlot(models.Model):
    class Meta:
        table = "tm.register"

    id = fields.BigIntField(pk=True)
    num = fields.IntField()
    team_name = fields.TextField()
    leader_id = fields.BigIntField()
    members = ArrayField(fields.BigIntField(), default=list)
    jump_url = fields.TextField(null=True)


class Scrim(models.Model):
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

    assigned_slots: fields.ManyToManyRelation["AssignedSlot"] = fields.ManyToManyField("models.AssignedSlot")
    reserved_slots: fields.ManyToManyRelation["ReservedSlot"] = fields.ManyToManyField("models.ReservedSlot")
    banned_teams: fields.ManyToManyRelation["BannedTeam"] = fields.ManyToManyField("models.BannedTeam")

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
            else:
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

        if self.slotlist_format != None:
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
    user_id = fields.BigIntField()
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

    expires = fields.DatetimeField(null=True)


# ************************************************************************************************


class TagCheck(models.Model):
    class Meta:
        table = "tagcheck"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    channel_id = fields.BigIntField()
    required_mentions = fields.IntField(default=0)
    delete_after = fields.BooleanField(default=False)

    @property
    def _guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def channel(self) -> Optional[discord.TextChannel]:
        return self.bot.get_channel(self.channel_id)

    @property
    def ignorerole(self) -> Optional[discord.Role]:
        if not self._guild is None:
            return discord.utils.get(self._guild.roles, name="quotient-tag-ignore")


class EasyTag(models.Model):
    class Meta:
        table = "easytags"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    channel_id = fields.BigIntField(index=True)
    delete_after = fields.BooleanField(default=False)

    @property
    def _guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def channel(self) -> Optional[discord.TextChannel]:
        return self.bot.get_channel(self.channel_id)

    @property
    def ignorerole(self) -> Optional[discord.Role]:
        if not self._guild is None:
            return discord.utils.get(self._guild.roles, name="quotient-tag-ignore")


class PointsInfo(models.Model):
    class Meta:
        table = "pt_info"

    id = fields.BigIntField(pk=True, index=True)
    guild_id = fields.BigIntField(index=True)
    channel_id = fields.BigIntField()
    kill_points = fields.IntField(default=1)
    posi_points = fields.JSONField(default=dict)
    default_format = fields.IntField(default=1)
    background = fields.TextField(null=True)
    box_color = fields.IntField(default=65459)
    title = fields.CharField(max_length=150, null=True)
    secondary_title = fields.CharField(max_length=200, null=True)
    footer = fields.CharField(max_length=200, default="Made with Quotient • quotientbot.xyz")
    data: fields.ManyToManyRelation["PointsTable"] = fields.ManyToManyField("models.PointsTable", index=True)

    @property
    def channel(self):
        return self.bot.get_channel(self.channel_id)


class PointsTable(models.Model):
    class Meta:
        table = "pt_data"

    id = fields.BigIntField(pk=True)
    points_table = fields.TextField()
    created_by = fields.BigIntField()
    created_at = fields.DatetimeField(index=True)
    edited_at = fields.DatetimeField(null=True)
    channel_id = fields.BigIntField(null=True)
    message_id = fields.BigIntField(null=True)

    @property
    def author(self):
        return self.bot.get_user(self.created_by)


class SSVerify(models.Model):
    class Meta:
        table = "ssverify.info"

    id = fields.BigIntField(pk=True, index=True)
    guild_id = fields.BigIntField()
    msg_channel_id = fields.BigIntField(index=True)
    log_channel_id = fields.BigIntField()
    role_id = fields.BigIntField()
    mod_role_id = fields.BigIntField()
    required_ss = fields.IntField()
    channel_name = fields.CharField(max_length=50)
    channel_link = fields.CharField(max_length=150)
    ss_type = fields.CharEnumField(SSType)
    success_message = fields.TextField(null=True)
    delete_after = fields.IntField(default=0)
    sstoggle = fields.BooleanField(default=True)
    data: fields.ManyToManyRelation["SSData"] = fields.ManyToManyField("models.SSData", index=True)

    @property
    def _guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def modrole(self):
        if self._guild is not None:
            return self._guild.get_role(self.mod_role_id)


class SSData(models.Model):
    class Meta:
        table = "ssverify.data"

    id = fields.BigIntField(pk=True)
    author_id = fields.BigIntField()
    channel_id = fields.BigIntField()
    message_id = fields.BigIntField()
    hash = fields.CharField(max_length=50, null=True)
    submitted_at = fields.DatetimeField(auto_now=True)
    status = fields.CharEnumField(SSStatus)


class SlotManager(models.Model):
    class Meta:
        table = "slot_manager"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    cancel_channel_id = fields.BigIntField()
    claim_channel_id = fields.BigIntField()
    post_channel_id = fields.BigIntField()

    cancel_message_id = fields.BigIntField()
    claim_message_id = fields.BigIntField()
    toggle = fields.BooleanField(default=True)

    @property
    def cancel_channel(self):
        return self.bot.get_channel(self.cancel_channel_id)

    @property
    def claim_channel(self):
        return self.bot.get_channel(self.claim_channel_id)

    @property
    def post_channel(self):
        return self.bot.get_channel(self.post_channel_id)
        