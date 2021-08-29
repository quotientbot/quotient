import discord
import config
from datetime import datetime
from constants import IST
from models.esports.slots import SlotLocks
from utils import aenumerate
from models import Scrim, SlotManager
from .constants import SlotLogType

from contextlib import suppress


class DirectSlotMessage(discord.ui.View):
    def __init__(self, record: SlotManager):
        super().__init__()
        link = f"https://discord.com/channels/{record.guild_id}/{record.main_channel_id}/{record.message_id}"
        self.add_item(discord.ui.Button(label="Click Me to Jump", url=link))


async def update_main_message(guild_id: int):
    record = await SlotManager.get_or_none(guild_id=guild_id)
    if not record:
        return

    embed = await get_slot_manager_message(guild_id)

    message = await record.message
    if message:
        view = discord.ui.View.from_message(message, timeout=None)
        return await message.edit(embed=embed, view=view)

    await SlotManager.filter(pk=record.id).delete()


async def lock_for_registration(guild_id: int, scrim_id: int):
    record = await SlotManager.get_or_none(guild_id=guild_id)
    if not record:
        return

    lock = await record.locks.filter(pk=scrim_id).first()
    if lock:
        await SlotLocks.filter(pk=lock.id).update(locked=True)
    else:
        lock = await SlotLocks.create(id=scrim_id)
        await record.locks.add(lock)

    await update_main_message(guild_id)


async def unlock_after_registration(guild_id: int, scrim_id: int):
    record = await SlotManager.get_or_none(guild_id=guild_id)
    if not record:
        return

    await SlotLocks.filter(pk=scrim_id).update(locked=False)
    await update_main_message(guild_id)


async def send_sm_logs(record: SlotManager, _type: SlotLogType, content: str):
    embed = discord.Embed(color=config.COLOR, description=content)
    if _type == SlotLogType.public:
        channel = record.updates_channel

    else:
        embed.title = "Slot-Manager Logs"
        channel = record.logschan

    with suppress(AttributeError, discord.Forbidden, discord.HTTPException):
        await channel.send(embed=embed, view=DirectSlotMessage(record))


async def get_slot_manager_message(guild_id: int, _free=None):

    if not isinstance(_free, list):
        _free = await free_slots(guild_id)

    _claimable = "\n".join(_free) or "**No Slots Available**"

    embed = discord.Embed(color=config.COLOR, title="Cancel or Claim a Scrims Slot")
    embed.description = f"● Press `cancel-your-slot` to cancel a slot.\n\n" f"● Claim Slots: \n{_claimable}"
    return embed


async def free_slots(guild_id: int):
    _list = []
    _time = datetime.now(tz=IST).replace(hour=0, minute=0, second=0, microsecond=0)

    slotmanager = await SlotManager.get_or_none(guild_id=guild_id)

    records = Scrim.filter(guild_id=guild_id, closed_at__gte=_time, available_slots__not=[])
    async for idx, scrim in aenumerate(records, start=1):
        if slotmanager:
            lock = await slotmanager.locks.filter(pk=scrim.id).first()
            if lock and lock.locked:
                continue

        _list.append(
            f"`{idx}` {getattr(scrim.registration_channel,'mention','deleted-channel')} ─ Slot {', '.join(map(str,scrim.available_slots))} (ID: {scrim.id})"
        )

    return _list


async def setup_slotmanager(ctx, post_channel: discord.TextChannel) -> None:

    reason = f"Created for Scrims Slot Management by {ctx.author}"

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(
            read_messages=True, send_messages=False, read_message_history=True
        ),
        ctx.guild.me: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            manage_channels=True,
            manage_messages=True,
            read_message_history=True,
            embed_links=True,
        ),
    }

    scrims = Scrim.filter(guild_id=ctx.guild.id)
    async for scrim in scrims:
        category = getattr(scrim.registration_channel, "category", None)
        if category:
            break
    try:
        main_channel = await ctx.guild.create_text_channel(
            name="cancel-claim-slot", overwrites=overwrites, reason=reason, category=category
        )
    except discord.Forbidden:
        return await ctx.error(f"I don't have permissions to create channel in scrims category. {category}")

    _embed = await get_slot_manager_message(ctx.guild.id)

    from .views import SlotManagerView

    msg: discord.Message = await main_channel.send(embed=_embed, view=SlotManagerView())

    sm = await SlotManager.create(
        guild_id=ctx.guild.id, main_channel_id=main_channel.id, updates_channel_id=post_channel.id, message_id=msg.id
    )
    return sm
