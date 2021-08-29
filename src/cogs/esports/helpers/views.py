import discord
import config
from datetime import datetime
from constants import IST
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
    ...


async def send_sm_logs(record: SlotManager, _type: SlotLogType, content: str):
    embed = discord.Embed(color=config.COLOR, description=content)
    if _type == SlotLogType.public:
        channel = record.updates_channel

    else:
        embed.title = "Slot-Manage Logs"
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

    records = Scrim.filter(guild_id=guild_id, closed_at__gte=_time, available_slots__not=[])
    async for idx, scrim in aenumerate(records, start=1):
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
