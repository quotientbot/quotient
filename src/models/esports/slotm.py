import asyncio

from models import BaseDbModel

from tortoise import fields
from models.helpers import ArrayField
from .scrims import Scrim

from typing import List, Tuple
import discord

from contextlib import suppress
from utils import plural, aenumerate, truncate_string

__all__ = ("ScrimsSlotManager",)


class ScrimsSlotManager(BaseDbModel):
    class Meta:
        table = "slot_manager"

    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField()
    main_channel_id = fields.BigIntField()

    message_id = fields.BigIntField()

    toggle = fields.BooleanField(default=True)
    allow_reminders = fields.BooleanField(default=True)
    multiple_slots = fields.BooleanField(default=False)

    scrim_ids = ArrayField(fields.BigIntField(), default=list)

    def __str__(self):
        return f"{getattr(self.main_channel,'mention','not-found')} - ({plural(self.scrim_ids):scrim|scrims})"

    @property
    def guild(self):
        return self.bot.get_guild(self.guild_id)

    async def scrims(self) -> List[Scrim]:
        return await Scrim.filter(pk__in=self.scrim_ids)

    @property
    def main_channel(self):
        return self.bot.get_channel(self.main_channel_id)

    @property
    def logschan(self):
        if (g := self.guild) is not None:
            return discord.utils.get(g.text_channels, name="quotient-scrims-logs")

    async def message(self):
        channel = await self.bot.getch(self.bot.get_channel, self.bot.fetch_channel, self.main_channel_id)
        if channel:
            _m = None
            with suppress(discord.HTTPException):
                _m = await self.bot.get_or_fetch_message(channel, self.message_id)
                # _m = await channel.fetch_message(self.message_id)

            return _m

    @staticmethod
    async def from_guild(guild: discord.Guild):
        return await ScrimsSlotManager.filter(guild_id=guild.id)

    @staticmethod
    async def unavailable_scrims(guild: discord.Guild) -> List[int]:
        return [scrim for record in await ScrimsSlotManager.filter(guild_id=guild.id) for scrim in record.scrim_ids]

    @staticmethod
    async def available_scrims(guild: discord.Guild) -> List[Scrim]:
        return await Scrim.filter(pk__not_in=await ScrimsSlotManager.unavailable_scrims(guild), guild_id=guild.id)

    async def full_delete(self):
        """
        Delete a slotm record.
        """
        message = await self.message()

        if message:
            _embed, _view = await self.public_message()
            for b in _view.children:
                if isinstance(b, discord.ui.Button):
                    b.disabled = True

            await message.edit(embed=_embed, view=_view)

        await self.delete()

    async def claimable_slots(self) -> List[str]:
        """
        Returns a list of slots that can be claimed
        """

        scrims = Scrim.filter(
            pk__in=self.scrim_ids,
            closed_at__gt=self.bot.current_time.replace(hour=0, minute=0, second=0, microsecond=0),
            available_slots__not=[],
            match_time__gt=self.bot.current_time,
            opened_at__isnull=True,
        ).order_by("open_time")

        _list = []

        async for idx, _ in aenumerate(scrims, start=1):
            _list.append(
                f"`{idx}` {getattr(_.registration_channel,'mention','deleted-channel')}  ─  {plural(_.available_slots):Slot|Slots}"
            )

        return _list

    async def public_message(self) -> Tuple[discord.Embed, discord.ui.View]:
        """
        Generate public message & view for slot manager.
        """

        from cogs.esports.views.slotm import ScrimsSlotmPublicView

        _claimable = await self.claimable_slots()

        _claimable_slots = (
            ("\n" + "\n".join(_claimable))
            if _claimable
            else "```No Slots Available at the time.\nPress 🔔 to set a reminder.```" ""
        )

        _e = discord.Embed(color=0x00FFB3, title="Scrims Slot Management", url=self.bot.config.SERVER_LINK)
        _e.description = f"● Press `cancel-slot` to cancel your slot.\n\n● Available Slots: {_claimable_slots}"

        view = ScrimsSlotmPublicView(self.bot, record=self)

        if not _claimable:
            view.children[1].disabled = True

        if not self.allow_reminders:
            view.children[2].disabled = True

        if not self.toggle:
            for _ in view.children:
                _.disabled = True

        return _e, view

    async def refresh_public_message(self) -> discord.Message:
        """
        Edit public slotm message to reflect current state.
        """
        m = await self.message()
        if not m:
            return await self.full_delete()

        _embed, _view = await self.public_message()

        with suppress(discord.HTTPException):
            return await m.edit(embed=_embed, view=_view)

    async def get_team_name(self, interaction: discord.Interaction) -> str:
        """
        Get team name of user when they claim slot.
        """
        _c = interaction.channel

        await _c.set_permissions(interaction.user, send_messages=True)
        _m = None
        with suppress(asyncio.TimeoutError):
            _m: discord.Message = await self.bot.wait_for(
                "message",
                check=lambda msg: msg.author.id == interaction.user.id and msg.channel.id == _c.id,
                timeout=30,
            )

        if not _m:
            await interaction.followup.send("Timed out. Please try again.", ephemeral=True)

        await _c.set_permissions(interaction.user, overwrite=None)

        with suppress(AttributeError, discord.HTTPException):
            await interaction.channel.purge(limit=5, check=lambda m: m.author == interaction.user and not m.pinned)
            return truncate_string(_m.content, 22)

    async def setup(self, guild: discord.Guild, user: discord.Member):
        """
        Creates a new channel and setup slot-m.
        """

        reason = f"Created for Scrims Slot Management by {user}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=True, send_messages=False, read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
                read_message_history=True,
                embed_links=True,
            ),
        }

        __channel = await guild.create_text_channel(name="cancel-claim-slot", overwrites=overwrites, reason=reason)

        self.main_channel_id = __channel.id

        _embed, _view = await self.public_message()
        m = await __channel.send(embed=_embed, view=_view)

        self.message_id = m.id
        await self.save()
        return self
