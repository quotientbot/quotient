from models import Scrim, Timer, Guild

import discord
from constants import IST

from .utils import positive, deny_request, not_guild
from datetime import datetime, timedelta


async def create_new_scrim(bot, data):
    guild = bot.get_guild(int(data.get("guild_id")))
    if not guild:
        return deny_request("Quotient have been removed from the server.")

    if not (await Guild.get(guild_id=guild.id)).private_ch:
        return deny_request(
            "You haven't done Quotient setup in your server yet, kindly run qsetup command once and try again."
        )

    perms = guild.me.guild_permissions
    if not all((perms.manage_channels, perms.manage_roles)):
        return deny_request("Quotient needs manage_channels and manage_roles permission in the server.")

    scrim = Scrim(guild_id=guild.id, host_id=int(data.get("host_id")), name=data.get("name"))

    registration_channel = bot.get_channel(int(data.get("registration_channel_id")))
    if not registration_channel:
        return deny_request("Quotient cannot see registration channel , Make sure it has appropriate permissions.")

    perms = registration_channel.permissions_for(guild.me)
    if not all(
        (perms.send_messages, perms.manage_messages, perms.manage_channels, perms.add_reactions, perms.embed_links)
    ):
        return deny_request("Quotient do not have required permissions in the registration channel.")

    if await Scrim.filter(registration_channel_id=registration_channel.id):
        return deny_request("The registration channel you selected is already assigned to another scrim.")

    scrim.registration_channel_id = registration_channel.id

    slotlist_channel = bot.get_channel(int(data.get("slotlist_channel_id")))
    if not slotlist_channel:
        return deny_request("Quotient cannot see slotlist channel , Can you make sure it has appropriate permissions?")

    perms = slotlist_channel.permissions_for(guild.me)
    if not all(
        (perms.send_messages, perms.manage_messages, perms.manage_channels, perms.add_reactions, perms.embed_links)
    ):
        return deny_request("Quotient do not have required permissions in the Slotlist channel.")

    scrim.slotlist_channel_id = slotlist_channel.id

    role = guild.get_role(int(data.get("role_id")))

    _list = [
        k
        for k, v in dict(role.permissions).items()
        if v is True and k in ("manage_channels", "manage_guild", "manage_messages", "manage_roles", "administrator")
    ]
    if _list:
        return deny_request("Success role contains some moderation permissions, kindly remove them first.")

    scrim.role_id = role.id

    epoch = datetime(1970, 1, 1)

    scrim.required_mentions = data.get("required_mentions")
    scrim.total_slots = data.get("total_slots")
    scrim.open_time = IST.localize(epoch + timedelta(hours=5, minutes=30, milliseconds=data.get("open_time")))

    await scrim.save()
    await bot.reminders.create_timer(scrim.open_time, "scrim_open", scrim_id=scrim.id)

    reason = "Created for scrims management."

    scrims_mod = discord.utils.get(guild.roles, name="scrims-mod")

    if scrims_mod is None:
        scrims_mod = await guild.create_role(name="scrims-mod", color=0x00FFB3, reason=reason)

    overwrite = registration_channel.overwrites_for(guild.default_role)
    overwrite.update(read_messages=True, send_messages=True, read_message_history=True)
    await registration_channel.set_permissions(scrims_mod, overwrite=overwrite)

    scrims_log_channel = discord.utils.get(guild.text_channels, name="quotient-scrims-logs")

    if scrims_log_channel is None:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            scrims_mod: discord.PermissionOverwrite(read_messages=True),
        }
        scrims_log_channel = await guild.create_text_channel(
            name="quotient-scrims-logs",
            overwrites=overwrites,
            reason=reason,
        )

        # Sending Message to scrims-log-channel
        note = await scrims_log_channel.send(
            embed=discord.Embed(
                description=f"If events related to scrims i.e opening registrations or adding roles, "
                f"etc are triggered, then they will be logged in this channel. "
                f"Also I have created {scrims_mod.mention}, you can give that role to your "
                f"scrims-moderators. User with {scrims_mod.mention} can also send messages in "
                f"registration channels and they won't be considered as scrims-registration.\n\n"
                f"`Note`: **Do not rename this channel.**",
                color=discord.Color(bot.color),
            )
        )
        await note.pin()

    return positive


async def edit_a_scrim(bot, data):
    guild = bot.get_guild(int(data.get("guild_id")))

    if not guild:
        return not_guild()

    scrim = await Scrim.get_or_none(id=int(data.get("id")))

    if not scrim:
        return deny_request("Either this scrim was deleted or Quotient was removed from the server.")

    _dict = {
        "name": data.get("name"),
        "required_mentions": int(data.get("required_mentions")),
        "start_from": int(data.get("start_from")),
        "total_slots": int(data.get("total_slots")),
        "autoslotlist": data.get("autoslotlist"),
        "multiregister": data.get("multiregister"),
        "autodelete_rejects": data.get("autodelete_rejects"),
        "teamname_compulsion": data.get("teamname_compulsion"),
        "no_duplicate_name": data.get("no_duplicate_name"),
        "show_time_elapsed": data.get("show_time_elapsed"),
        "open_message": data.get("open_message"),
        "close_message": data.get("close_message"),
        "autodelete_extras": data.get("autodelete_extras"),
    }

    registration_channel_id = int(data.get("registration_channel_id"))
    if not scrim.registration_channel_id == registration_channel_id:
        registration_channel = bot.get_channel(int(data.get("registration_channel_id")))

        if not registration_channel:
            return deny_request("Quotient cannot see registration channel , Make sure it has appropriate permissions.")

        perms = registration_channel.permissions_for(guild.me)
        if not all(
            (
                perms.send_messages,
                perms.manage_messages,
                perms.manage_channels,
                perms.add_reactions,
                perms.embed_links,
            )
        ):
            return deny_request("Quotient do not have required permissions in the registration channel.")

        if await Scrim.filter(registration_channel_id=registration_channel.id):
            return deny_request("The registration channel you selected is already assigned to another scrim.")

        _dict["registration_channel_id"] = registration_channel.id

    slotlist_channel_id = int(data.get("slotlist_channel_id"))
    if not scrim.slotlist_channel_id == slotlist_channel_id:
        slotlist_channel = bot.get_channel(int(data.get("slotlist_channel_id")))
        if not slotlist_channel:
            return await deny_request(
                "Quotient cannot see slotlist channel , Can you make sure it has appropriate permissions?"
            )

        perms: discord.Permissions = slotlist_channel.permissions_for(guild.me)
        if not all(
            (
                perms.send_messages,
                perms.manage_messages,
                perms.manage_channels,
                perms.add_reactions,
                perms.embed_links,
            )
        ):
            return await deny_request("Quotient do not have required permissions in the Slotlist channel.")

        _dict["slotlist_channel_id"] = slotlist_channel_id

    role_id = int(data.get("role_id"))
    if not scrim.role_id == role_id:
        role = guild.get_role(int(data.get("role_id")))

        _list = [
            k
            for k, v in dict(role.permissions).items()
            if v is True and k in ("manage_channels", "manage_guild", "manage_messages", "manage_roles", "administrator")
        ]
        if _list:
            return await deny_request("Success role contains some moderation permissions, kindly remove them first.")

        _dict["role_id"] = role.id

    ping_role_id = data.get("ping_role_id")
    if ping_role_id and int(ping_role_id) != scrim.ping_role_id:
        _dict["ping_role_id"] = int(ping_role_id)

    _dict["open_role_id"] = int(data.get("open_role_id"))

    epoch = datetime(1970, 1, 1)

    open_time = IST.localize(epoch + timedelta(hours=5, minutes=30, milliseconds=int(data.get("open_time"))))

    _dict["open_time"] = open_time

    if data.get("autoclean_time"):
        autoclean_time = IST.localize(
            epoch + timedelta(hours=5, minutes=30, milliseconds=int(data.get("autoclean_time")))
        )
        if datetime.now(tz=IST) > autoclean_time:
            autoclean_time = autoclean_time + timedelta(hours=24)

        _dict["autoclean_time"] = autoclean_time
        await Timer.filter(extra={"args": [], "kwargs": {"scrim_id": int(data.get("id"))}}, event="autoclean").delete()

        await bot.reminders.create_timer(autoclean_time, "autoclean", scrim_id=int(data.get("id")))

    await Scrim.filter(id=int(data.get("id"))).update(**_dict)
    await bot.db.execute(
        """UPDATE public."sm.scrims" SET autoclean = $1 , open_days = $2 WHERE id = $3""",
        data.get("autoclean"),
        data.get("open_days"),
        int(data.get("id")),
    )
    await Timer.filter(extra={"args": [], "kwargs": {"scrim_id": int(data.get("id"))}}, event="scrim_open").delete()

    await bot.reminders.create_timer(open_time, "scrim_open", scrim_id=int(data.get("id")))

    return positive


async def delete_a_scrim(scrim_id):
    await Scrim.filter(pk=int(scrim_id)).delete()

    return positive
