from core.Context import Context
from models import Tourney

from constants import EsportsRole, RegDeny

import discord
import re


def get_tourney_slots(slots):
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

    elif message.author.id in get_tourney_slots(await tourney.assigned_slots.all()) and not tourney.multiregister:
        _bool = False
        bot.dispatch("tourney_registration_deny", message, RegDeny.multiregister, tourney)

    return _bool


async def send_success_message(ctx: Context, text: str):
    embed = ctx.bot.embed(ctx, title="Registration Successful", description=text)
    await ctx.message.reply(embed=embed, delete_after=10)


async def t_ask_embed(ctx, value, description: str):
    embed = discord.Embed(
        color=0x00FFB3,
        title=f"🛠️ Tournament Manager ({value}/5)",
        description=description,
    )
    embed.set_footer(text=f'Reply with "cancel" to stop the process.')
    await ctx.send(embed=embed, embed_perms=True)
