import discord
from models import Scrim
from tortoise.expressions import Q

from .regex import find_team_name


async def toggle_channel_perms(channel: discord.TextChannel, role: discord.Role, _bool=True) -> bool:
    overwrite = channel.overwrites_for(role)
    overwrite.update(send_messages=_bool)
    try:
        await channel.set_permissions(
            role,
            overwrite=overwrite,
            reason=("Registration is over!", "Open for Registrations!")[_bool],  # False=0, True=1
        )

        return True

    except:
        return False


async def ensure_self_permissions(scrim: Scrim) -> bool:
    guild = scrim.guild
    me = guild.me
    logs_channel = scrim.logs_channel
    registration_channel = scrim.registration_channel

    open_role_id = scrim.open_role_id

    all_ok = True
    e = scrim.bot.error_embed(
        title="Scrims Registration Stopped!", description="Fix the issues below before restarting:\n\n"
    )

    if not registration_channel:
        all_ok = False
        e.description += "- Registration channel not found.\n"

    if registration_channel and not registration_channel.permissions_for(me).manage_channels:
        all_ok = False
        e.description += "- I don't have `Manage Channels` permission in the registration channel.\n"

    if registration_channel and not registration_channel.permissions_for(me).manage_messages:
        all_ok = False
        e.description += "- I don't have `Manage Messages` permission in the registration channel.\n"

    if registration_channel and not registration_channel.permissions_for(me).add_reactions:
        all_ok = False
        e.description += "- I don't have `Add Reactions` permission in the registration channel.\n"

    if registration_channel and not registration_channel.permissions_for(me).use_external_emojis:
        all_ok = False
        e.description += "- I don't have `Use External Emojis` permission in the registration channel.\n"

    if registration_channel and not registration_channel.permissions_for(me).manage_permissions:
        all_ok = False
        e.description += "- I don't have `Manage Permissions` permission in the registration channel.\n"

    if open_role_id and not guild.get_role(open_role_id):
        all_ok = False
        e.description += f"- Open role ({open_role_id}) not found.\n"

    if not all_ok:
        try:
            await logs_channel.send(
                getattr(scrim.scrims_mod_role, "mention", ""),
                embed=e,
                view=scrim.bot.contact_support_view(),
                allowed_mentions=discord.AllowedMentions(roles=True),
            )
        except (discord.HTTPException, AttributeError):
            pass

        try:
            await registration_channel.send(
                getattr(scrim.scrims_mod_role, "mention", ""),
                embed=e,
                view=scrim.bot.contact_support_view(),
                allowed_mentions=discord.AllowedMentions(roles=True),
            )
        except (discord.HTTPException, AttributeError):
            pass

        # TODO: Stop scrims registration immediately.

    return all_ok


async def deny_scrims_registration(scrim: Scrim, msg: discord.Message, deny_reason: str, logs_reason: str):
    logs_channel = scrim.logs_channel

    if scrim.autodelete_rejected_registrations:
        await msg.delete(delay=10)

    try:
        await msg.add_reaction(scrim.cross_emoji)
        await msg.reply(embed=scrim.bot.error_embed(description=deny_reason), delete_after=6)
    except discord.HTTPException:
        pass

    try:
        await logs_channel.send(
            embed=scrim.bot.error_embed(
                f"Registration of {msg.author.mention} denied in {msg.channel.mention}.\n\nReason: `{logs_reason}`"
            ),
        )
    except (discord.HTTPException, AttributeError):
        pass


async def ensure_scrims_requirements_in_msg(scrim: Scrim, msg: discord.Message) -> bool:
    team_name = find_team_name(msg.content)

    if not scrim.allow_without_teamname:
        if not team_name:
            await deny_scrims_registration(
                scrim,
                msg,
                "You need to provide a Team Name to register.",
                "No Team Name Provided in registration message.",
            )
            return False

    if scrim.required_mentions and True in [m.bot for m in msg.mentions]:
        await deny_scrims_registration(
            scrim,
            msg,
            "You cannot mention bots in the registration message.",
            "Bot mentioned in registration message.",
        )
        return False

    if not scrim.required_mentions <= len(msg.mentions):
        await deny_scrims_registration(
            scrim,
            msg,
            f"You need to mention atleast {scrim.required_mentions} teammates in the registration message.",
            f"Only {len(msg.mentions)}/{scrim.required_mentions} members mentioned in registration message.",
        )
        return False

    if record := await scrim.banned_teams.filter(members__contains=msg.author.id).first():
        await deny_scrims_registration(
            scrim,
            msg,
            f"You are banned from registering in this scrim. ({discord.utils.format_dt(record.banned_till) if record.banned_till else 'Permanent'})",
            "Member is banned from the scrim.",
        )
        return False

    if scrim.required_lines and len(msg.content.split("\n")) < scrim.required_lines:
        await deny_scrims_registration(
            scrim,
            msg,
            f"Your registration message is too short. It seems you missed some required information.",
            f"Only {len(msg.content.splitlines())}/{scrim.required_lines} lines provided in registration message.",
        )
        return False

    if not scrim.allow_multiple_registrations and await scrim.assigned_slots.filter(leader_id=msg.author.id).count():
        await deny_scrims_registration(
            scrim,
            msg,
            "You have already registered for this scrim.",
            "Member has already registered for the scrim.",
        )
        return False

    if (
        team_name
        and not scrim.allow_duplicate_teamname
        and await scrim.assigned_slots.filter(team_name=find_team_name(msg.content)).count()
    ):
        await deny_scrims_registration(
            scrim,
            msg,
            "Someone has already registered with the same teamname.",
            "Team Name already taken in the scrim. (Duplicate Team Name)",
        )
        return False

    if not scrim.allow_duplicate_mentions:
        if slot := await scrim.assigned_slots.filter(
            Q(*[Q(members__contains=user_id) for user_id in msg.raw_mentions], join_type="OR")
        ).first():

            await deny_scrims_registration(
                scrim,
                msg,
                f"Someone has already registered with the same teammates {slot.jump_url}",
                "Duplicate mentions in registration message. (Fake / Duplicate Tags)",
            )
            return False

    return True
