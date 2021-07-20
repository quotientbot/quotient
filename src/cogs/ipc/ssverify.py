from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from .base import IpcCog
from discord.ext import ipc

from models import SSVerify
from constants import SSType


class SSverifyIpc(IpcCog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @property
    def success_msg(self) -> str:
        return "**You have satisfied the screenshot requirement. Kindly move on to the next step.**"

    async def validate_requirments(self, data: dict) -> bool:
        _bool = True
        return _bool

    @ipc.server.route()
    async def create_ssverify(self, payload):
        data = payload.data
        guild_id = int(data["guild_id"])
        user_id = int(data["user_id"])
        msg_channel_id = int(data["msg_channel_id"])
        log_channel_id = int(data["log_channel_id"])
        role_id = int(data["role_id"])
        mod_role_id = int(data["mod_role_id"])

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return self.not_guild

        member = guild.get_member(user_id)
        if not member:
            return self.not_member

        if not member.guild_permissions.manage_guild:
            return self.not_manage_guild

        if not guild.me.guild_permissions.manage_roles:
            return self.deny_request("Quotient need manage roles permission in your server to work properly.")

        if not (msg_channel := guild.get_channel(msg_channel_id)):
            return self.deny_request(
                "Quotient couldn't see screenshots verify channel, make sure it has appropriate permissions"
            )

        perms = msg_channel.permissions_for(guild.me)
        if not all((perms.add_reactions, perms.send_messages, perms.embed_links, perms.manage_messages)):
            return self.deny_request(
                "kindly make sure Quotient has add_reactions, send_messages, embed_links and manage_messages permission in screenshot channel."
            )

        ssverify = SSVerify(
            guild_id=guild.id,
            msg_channel_id=msg_channel.id,
            delete_after=int(data.get("delete_after", 0)),
            ss_type=SSType(data.get("ss_type", "youtube")),
            success_message=data.get("success_message", self.success_msg),
            channel_name=data.get("channel_name"),
            channel_link=data.get("channel_link"),
            required_ss=int(data.get("required_ss", 1)),
            mod_role_id=mod_role_id,
        )

        if not (log_channel := guild.get_channel(log_channel_id)):
            return self.deny_request(
                "Quotient couldn't see Screenshot logs channel. Kindly make sure it has appropriate permissions."
            )

        perms = log_channel.permissions_for(guild.me)
        if not all((perms.send_messages, perms.embed_links)):
            return self.deny_request(
                f"Kindly make sure Quotient has send_messages and embed_links permissions in log channel ({log_channel.name})"
            )

        ssverify.log_channel_id = log_channel.id

        role = guild.get_role(role_id)
        if not role:
            return self.deny_request("Quotient couldn't find the role you specified.")

        check = self.check_if_mod(role)
        if not check == True:
            return self.deny_request(
                f"Success role has moderation permissions. Kindly remove them first. ({', '.join(check)})"
            )

        if role >= (top_role := guild.me.top_role):
            return self.deny_request(
                f"My toprole ({top_role.name}) is below {role.name}. Kindky move it above the success role from server settings."
            )

        await ssverify.save()
        self.bot.ssverify_channels.add(ssverify.msg_channel_id)
        return self.positive

    @ipc.server.route()
    async def edit_ssverify(self, payload):
        data = payload.data

        id = int(data.get("id"))
        guild_id = int(data.get("guild_id"))
        user_id = int(data.get("user_id"))

        guild = self.bot.get_guild(guild_id)
        ssverify = await SSVerify.get_or_none(pk=id, guild_id=guild_id)

        if not all((guild, ssverify)):
            return self.deny_request("Either the ssverify setup was deleted or Quotient was removed from the server.")

        member = guild.get_member(user_id)
        if not member or not member.guild_permissions.manage_guild:
            return self.deny_request(f"You need to have manage server permissions in {guild.name} to make changes.")

    @ipc.server.route()
    async def delete_ssverify(self, payload):
        data = payload.data

        user_id = int(data.get("user_id"))
        guild_id = int(data.get("guild_id"))

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return self.deny_request("Quotient was removed from the server.")

        member = guild.get_member(user_id)
        if not member or not member.guild_permissions.manage_guild:
            return self.deny_request(f"You need to have manage server permissions in {guild.name} to make changes.")

        await SSVerify.filter(pk=int(payload.id), guild_id=guild_id).delete()
        return self.positive
