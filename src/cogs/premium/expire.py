from __future__ import annotations

import typing

from models.esports.scrims import Scrim

if typing.TYPE_CHECKING:
    from core import Quotient

from contextlib import suppress
from models import SlotManager, Tourney, Guild, User, Guild, TagCheck
import discord
import config
from utils import discord_timestamp, plural

from .views import PremiumView
from cogs.esports.views import SlotManagerView, TourneySlotManager
from cogs.esports.helpers.views import free_slots, get_slot_manager_message


async def activate_premium(bot: Quotient, guild: discord.Guild):

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
            embed.color = config.PREMIUM_COLOR
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
                _e.color = config.PREMIUM_COLOR
                message = await slotm_channel.send(embed=_e, view=_view)
                await Tourney.get(pk=tourney.id).update(slotm_channel_id=slotm_channel.id, slotm_message_id=message.id)


async def deactivate_premium(guild_id: int):
    ...


async def extra_guild_perks(guild: discord.Guild, model: Guild):

    _list = [
        "You will lose access of Quotient Prime Bot.",
        "You won't be able to set custom color and footer for embeds."
        "Tourney reactions emojis will be changed to default.",
    ]

    if _s := await Scrim.filter(guild_id=guild.id).order_by("id")[3:]:
        _list.append(f"{plural(len(_s)):scrim|scrims} will be deleted. (ID: {', '.join((str(s.pk) for s in _s))})")

    if _t := await Tourney.filter(guild_id=guild.id).order_by("id")[2:]:
        _list.append(f"{plural(len(_t)):tourney|tourneys} will be deleted. (ID: {', '.join(str(t.pk) for t in _t)})")

    if _tc := await TagCheck.filter(guild_id=guild.id).order_by("id")[1:]:
        _list.append(
            f"{len(_tc)} tagcheck setup will be removed. (Channels: {', '.join((ch.channel.name for ch in _tc))})"
        )

    return _list


async def remind_guild_to_pay(guild: discord.Guild, model: Guild):
    if (_ch := model.private_ch) and _ch.permissions_for(_ch.guild.me).embed_links:
        _e = discord.Embed(color=discord.Color.red(), title="⚠️__**Quotient Prime Ending Soon**__⚠️")
        _e.description = f"This is to inform you that your subscription of **Quotient Prime** is ending {discord_timestamp(model.premium_end_time)}"

        _perks = "*\n".join(await extra_guild_perks(model))

        _e.description += f"```{_perks}```"

        _view = PremiumView(label="Buy Prime and Save Server from Apocalypse")
        await _ch.send(embed=_e, view=_view)


async def remind_user_to_pay(user: discord.User, model: User):
    _e = discord.Embed(color=discord.Color.red(), title="⚠️__**IMPORTANT**__⚠️")
    _e.description = (
        f"This is to remind you that your subscription of **Quotient Prime** is ending {discord_timestamp(model.premium_expire_time)}"
        f"\n[*Click Me To Continue Enjoying Prime*]({config.WEBSITE}/premium)"
    )
    with suppress(discord.HTTPException):
        _view = PremiumView(label="Purchase Prime")
        await user.send(embed=_e, view=_view)
