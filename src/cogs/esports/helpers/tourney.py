from __future__ import annotations

from contextlib import suppress
from core import Context
from models import Tourney, TMSlot

from constants import EsportsRole, RegDeny

from typing import List, TYPE_CHECKING, Optional

from datetime import datetime

import io

import discord
import re


def get_tourney_slots(slots: List[TMSlot]) -> int:
    for slot in slots:
        yield slot.leader_id


def tourney_work_role(tourney: Tourney, _type: EsportsRole):

    if _type == EsportsRole.ping:
        role = tourney.ping_role

    elif _type == EsportsRole.open:
        role = tourney.open_role

    if not role:
        return None

    if role == tourney.guild.default_role:
        return "@everyone"

    return getattr(role, "mention", "role-deleted")


def before_registrations(message: discord.Message, role: discord.Role) -> bool:
    me = message.guild.me
    channel = message.channel

    if (
        not me.guild_permissions.manage_roles
        or role > message.guild.me.top_role
        or not channel.permissions_for(me).add_reactions
        or not channel.permissions_for(me).use_external_emojis
    ):
        return False
    return True


async def check_tourney_requirements(bot, message: discord.Message, tourney: Tourney) -> bool:
    _bool = True

    if tourney.teamname_compulsion:
        teamname = re.search(r"team.*", message.content)
        if not teamname or not teamname.group().strip():
            _bool = False
            bot.dispatch("tourney_registration_deny", message, RegDeny.noteamname, tourney)

    if tourney.required_mentions and not all(map(lambda m: not m.bot, message.mentions)):
        _bool = False
        bot.dispatch("tourney_registration_deny", message, RegDeny.botmention, tourney)

    elif not len(message.mentions) >= tourney.required_mentions:
        _bool = False
        bot.dispatch("tourney_registration_deny", message, RegDeny.nomention, tourney)

    elif message.author.id in tourney.banned_users:
        _bool = False
        bot.dispatch("tourney_registration_deny", message, RegDeny.banned, tourney)

    return _bool


async def t_ask_embed(ctx, value, description: str):
    embed = discord.Embed(
        color=ctx.bot.color,
        title=f"🛠️ Tournament Manager ({value}/5)",
        description=description,
    )
    embed.set_footer(text=f'Reply with "cancel" to stop the process.')
    await ctx.send(embed=embed, embed_perms=True)


async def update_confirmed_message(tourney: Tourney, link: str):
    _ids = [int(i) for i in link.split("/")[5:]]

    message = None

    with suppress(discord.HTTPException, IndexError):
        message = await tourney.guild.get_channel(_ids[0]).fetch_message(_ids[1])

        if message:
            e = message.embeds[0]

            e.description = "~~" + e.description.strip() + "~~"
            e.title = "Cancelled Slot"
            e.color = discord.Color.red()

            await message.edit(embed=e)


async def csv_tourney_data(tourney: Tourney):
    guild = tourney.guild

    guild_members = [m.id for m in guild.members]

    def _slot_info(slot: TMSlot):
        _team = " | ".join((f"{str(guild.get_member(m))} ({m})" for m in slot.members))

        in_server = sum(1 for i in slot.members if i in guild_members)

        return (
            f"{slot.num},{slot.team_name},{str(guild.get_member(slot.leader_id))},"
            f"'{slot.leader_id}',{_team},{in_server},{slot.jump_url}"
        )

    _x = "Reg Posi,Team Name,Leader,Leader ID,Teammates,Teammates in Server,Jump URL\n"

    async for _slot in tourney.assigned_slots.all().order_by("num"):
        _x += f"{_slot_info(_slot)}\n"

    fp = io.BytesIO(_x.encode())

    return discord.File(fp, filename=f"tourney_data_{tourney.id}_{datetime.now().timestamp()}.csv")


async def get_tourney_from_channel(guild_id: int, channel_id: int) -> Optional[Tourney]:
    tourneys = await Tourney.filter(guild_id=guild_id)

    for tourney in tourneys:
        if await tourney.media_partners.filter(pk=channel_id).exists():
            return tourney
