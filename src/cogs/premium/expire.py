from __future__ import annotations

import typing
from contextlib import suppress

import config
import discord
from models import (
    EasyTag,
    Guild,
    Scrim,
    ScrimsSlotManager,
    SSVerify,
    TagCheck,
    Tourney,
    User,
)
from utils import discord_timestamp, plural

from .views import PremiumView


async def deactivate_premium(guild_id: int):
    await Guild.filter(guild_id=guild_id).update(embed_color=config.COLOR, embed_footer=config.FOOTER, is_premium=False)

    _s: typing.List[Scrim] = (await Scrim.filter(guild_id=guild_id).order_by("id"))[3:]
    await Scrim.filter(id__in=(s.pk for s in _s)).delete()

    _t: typing.List[Tourney] = (await Tourney.filter(guild_id=guild_id).order_by("id"))[1:]
    await Tourney.filter(id__in=(t.pk for t in _t)).delete()

    _tc: typing.List[TagCheck] = (await TagCheck.filter(guild_id=guild_id).order_by("id"))[1:]
    await TagCheck.filter(id__in=(t.pk for t in _tc)).delete()

    _ez: typing.List[EasyTag] = (await EasyTag.filter(guild_id=guild_id).order_by("id"))[1:]
    await EasyTag.filter(id__in=(e.pk for e in _ez)).delete()

    await Tourney.filter(guild_id=guild_id).update(emojis={})

    ssverify = await SSVerify.filter(guild_id=guild_id)
    for _ in ssverify:
        await _.full_delete()

    _slotm = (await ScrimsSlotManager.filter(guild_id=guild_id).order_by("id"))[1:]
    for _ in _slotm:
        await _.full_delete()

    return


async def extra_guild_perks(guild_id: int):

    _list = [
        "- Can't use Quotient Pro bot.",
        "- Tourney reactions emojis will be changed to default.",
        "- No more than 1 Media Partner Channel per tourney.",
    ]

    if (_s := await Scrim.filter(guild_id=guild_id).order_by("id"))[3:]:
        _list.append(f"- {plural(len(_s)):scrim|scrims} will be deleted. (ID: {', '.join((str(s.pk) for s in _s))})")

    if (_t := await Tourney.filter(guild_id=guild_id).order_by("id"))[1:]:
        _list.append(f"- {plural(len(_t)):tourney|tourneys} will be deleted. (ID: {', '.join(str(t.pk) for t in _t)})")

    if (_tc := await TagCheck.filter(guild_id=guild_id).order_by("id"))[1:]:
        _list.append(
            f"- {len(_tc)} tagcheck setup will be removed. (Channels: {', '.join((str(ch.channel) for ch in _tc))})"
        )

    if (_ez := await EasyTag.filter(guild_id=guild_id).order_by("id"))[1:]:
        _list.append(
            f"- {len(_ez)} easytag setup will be removed. (Channels: {', '.join((str(ch.channel) for ch in _ez))})"
        )

    if (_slotm := await ScrimsSlotManager.filter(guild_id=guild_id).order_by("id"))[1:]:
        _list.append(
            f"- {len(_slotm)} scrims slot manager setup will be removed. (Channels: {', '.join((str(ch.main_channel) for ch in _slotm))})"
        )

    if _ss := await SSVerify.filter(guild_id=guild_id).order_by("id"):
        _list.append(
            f"- {len(_ss)} SSVerify setup will be removed. (Channels: {', '.join((str(ch.channel) for ch in _ss))})"
        )

    return _list


async def remind_guild_to_pay(guild: discord.Guild, model: Guild):
    if (_ch := model.private_ch) and _ch.permissions_for(_ch.guild.me).embed_links:
        _e = discord.Embed(
            color=discord.Color.red(),
            title="⚠️__**Quotient Pro Ending Soon**__⚠️",
            url=config.SERVER_LINK,
        )

        _e.description = (
            f"This is to inform you that your subscription of **Quotient Pro** is ending soon "
            f"({discord_timestamp(model.premium_end_time,'D')})"
            "\n\n*Kindly renew your subscription to continue using Quotient Premium features.*"
        )

        _roles = [
            role.mention for role in guild.roles if all((role.permissions.administrator, not role.managed, role.members))
        ]

        _view = PremiumView(label="Renew Quotient Pro")
        await _ch.send(
            embed=_e,
            view=_view,
            content=", ".join(_roles[:2]) if _roles else getattr(guild.owner, "mention", ""),
            allowed_mentions=discord.AllowedMentions(roles=True),
        )


async def remind_user_to_pay(user: discord.User, model: User):
    _e = discord.Embed(color=discord.Color.red(), title="⚠️__**IMPORTANT**__⚠️")
    _e.description = (
        f"This is to remind you that your subscription of **Quotient Pro** is ending {discord_timestamp(model.premium_expire_time)}"
        f"\n[*Click Me To Continue Enjoying Quotient Pro*](https://quotientbot.xyz/premium)"
    )
    with suppress(discord.HTTPException):
        await user.send(embed=_e)
