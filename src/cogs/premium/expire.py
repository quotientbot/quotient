from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from contextlib import suppress
from models import SlotManager, Tourney, Guild
import discord
from constants import bot_colors

from cogs.esports.views import SlotManagerView, TourneySlotManager
from cogs.esports.helpers.views import free_slots, get_slot_manager_message


async def activate_premium(bot: Quotient, guild: discord.Guild):

    __bot_id = bot.user.id

    await Guild.get(pk=guild.id).update(
        embed_color=bot_colors[__bot_id],
        bot_id=__bot_id,
        waiting_activation=False,
    )

    await bot.cache.update_guild_cache(guild.id)

    _slotmanager = await SlotManager.get_or_none(guild_id=guild.id)

    if _slotmanager:
        msg: discord.Message = await _slotmanager.message

        with suppress(discord.HTTPException):

            view = SlotManagerView(bot)

            _free = await free_slots(guild.id)

            view.children[1].disabled = False
            if not _free:
                view.children[1].disabled = True

            embed = await get_slot_manager_message(guild.id, _free)

            await msg.delete()
            _m: discord.Message = await _slotmanager.main_channel.send(embed=embed, view=view)
            await SlotManager.get(guild_id=guild.id).update(message_id=_m.id)

    tourneys = await Tourney.filter(guild_id=guild.id)
    if tourneys:
        for tourney in tourneys:
            if (_c := tourney.slotm_channel) and _c.permissions_for(guild.me).manage_channels:
                await _c.delete()
                _view = TourneySlotManager(bot, tourney=tourney)

                _category = _c.category
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        read_messages=True, send_messages=False, read_message_history=True
                    ),
                    guild.me: discord.PermissionOverwrite(manage_channels=True, manage_permissions=True),
                }

                slotm_channel = await _category.create_text_channel(_c.name, position=_c.position, overwrites=overwrites)

                _e = TourneySlotManager.initial_embed(tourney)
                message = await slotm_channel.send(embed=_e, view=_view)
                await Tourney.get(pk=tourney.id).update(slotm_channel_id=slotm_channel.id, slotm_message_id=message.id)


async def deactivate_premium(guild_id: int):
    ...
