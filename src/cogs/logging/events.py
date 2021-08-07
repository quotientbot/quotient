from contextlib import suppress
import discord, humanize
from datetime import datetime, timedelta
from core import Quotient, Cog
from discord.utils import escape_markdown
from constants import IST, LogType
from models import Snipes
from .functions import *
from utils import strtime, human_timedelta

__all__ = ("LoggingEvents",)


class LoggingEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.vc = {}
        self.bot.loop.create_task(self.delete_older_snipes())

    async def delete_older_snipes(self):  # we delete snipes that are older than 15 days
        await Snipes.filter(delete_time__lte=(datetime.now(tz=IST) - timedelta(days=15))).all().delete()

    @Cog.listener()
    async def on_snipe_deleted(self, message: discord.Message):
        if not message.guild:
            return
        channel = message.channel
        content = message.content if message.content else "*[Content Unavailable]*"

        await Snipes.create(channel_id=channel.id, author_id=message.author.id, content=content, nsfw=channel.is_nsfw())

    # =======================================================

    @Cog.listener()
    async def on_log(self, _type: LogType, **kwargs):
        # with suppress TypeError:
        embed, channel = await self.handle_event(_type, **kwargs)
        if embed is not None and channel is not None:
            await channel.send(embed=embed)

    async def handle_event(self, _type: LogType, **kwargs):
        embed = discord.Embed(timestamp=datetime.now(tz=IST))

        if _type == LogType.msg:
            subtype = kwargs.get("subtype")
            message = kwargs.get("message")

            guild = message.guild if subtype == "single" else message[0].guild

            channel, color = await get_channel(_type, guild)
            if not channel:
                return

            check = await check_permissions(_type, channel)
            if not check:
                return

            if subtype == "single":

                embed.color = discord.Color(color)
                embed.set_footer(text=f"ID: {message.id}", icon_url=self.bot.user.avatar_url)

                embed.description = f"Message sent by {message.author.mention} deleted in {message.channel.mention}."
                embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)

                cont = escape_markdown(message.content)

                if cont and len(cont) > 128:
                    cont = truncate_string(cont)

                embed.add_field(name="Message:", value=cont or f"*[Content Unavailable]*", inline=False)

                if message.attachments and "image" in message.attachments[0].content_type:
                    embed.set_image(url=message.attachments[0].proxy_url)

                return embed, channel

            if subtype == "bulk":

                msg = message[0]
                msg_str = f"\n\n{'-'*50}\n\n".join((f"Author: {str(m.author)}\nContent: {m.content}" for m in message))

                embed.color = discord.Color(color)
                embed.description = f"{len(message)} messages, deleted in {msg.channel.mention}"
                embed.add_field(name="Messages", value=f"[Click Me ...]({str(await self.bot.binclient.post(msg_str))})")
                embed.set_footer(text=f"Bulk Delete: {len(message)}", icon_url=self.bot.user.avatar_url)
                return embed, channel
            before, after = message
            embed.color = discord.Color(color)
            embed.set_footer(text=f"ID: {before.id}", icon_url=self.bot.user.avatar_url)
            embed.description = f"A [message]({before.jump_url}) was edited in {before.channel.mention}."
            embed.set_author(name=str(before.author), icon_url=before.author.avatar_url)
            embed.add_field(
                name="Before:", value=truncate_string(before.content) or "*[Content Unavailable]*", inline=False
            )
            embed.add_field(name="After:", value=truncate_string(after.content) or "*[Content Unavailable]*")

            return embed, channel

        if _type == LogType.join:
            member = kwargs.get("member")

            guild = member.guild

            channel, color = await get_channel(_type, guild)
            if not channel:
                return

            check = await check_permissions(_type, channel)
            if not check:
                return

            embed.color = discord.Color(color)
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            embed.set_thumbnail(url=member.avatar_url)
            embed.description = (
                f"{member.mention} just joined the server, they are {guild.member_count}th member of {guild.name}."
            )
            embed.add_field(
                name="Account Age:",
                value=f"`{strtime(member.created_at)}` ({human_timedelta(IST.localize(member.created_at))})",
            )
            embed.set_footer(text=f"ID: {member.id}")

            return embed, channel

        if _type == LogType.leave:
            member = kwargs.get("member")

            guild = member.guild

            channel, color = await get_channel(_type, guild)
            if not channel:
                return

            check = await check_permissions(_type, channel)
            if not check:
                return

            embed.color = color
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            embed.set_thumbnail(url=member.avatar_url)

            embed.description = f"{member.mention} just left the server. They joined {human_timedelta(IST.localize(member.joined_at) + timedelta(hours=5, minutes=30))}"
            embed.add_field(
                name="Roles:", value=", ".join((role.mention for role in member.roles)).replace("@@everyone", "@everyone")
            )

            return embed, channel

        if _type == LogType.invite:
            subtype = kwargs.get("subtype")

            invite = kwargs.get("invite")

            if subtype in ("create", "delete"):
                guild = invite.guild

            else:
                message = kwargs.get("message")
                guild = message.guild

            check = await get_channel(_type, guild)
            if not check:
                return

            channel, color = check

            check = await check_permissions(_type, channel)
            if not check:
                return

            embed.color = discord.Color(color)

            if subtype == "create":
                embed.title = "Server Invite Created"
                embed.set_author(name=str(invite.inviter), icon_url=invite.inviter.avatar_url)
                embed.set_footer(text=f"ID: {invite.inviter.id}")
                embed.description = (
                    f"{invite.inviter.mention} just created an invite (`{invite.code}`) for {invite.channel.mention}"
                )

                embed.add_field(name="Max Uses", value=f"{'Infinite' if not invite.max_uses else invite.max_uses}")
                embed.add_field(
                    name="Max Age",
                    value=f"{'Infinite' if invite.max_age == 0 else humanize.precisedelta(invite.max_age)}",
                )

                return embed, channel
            if subtype == "delete":
                pass
                # print(invite.created_at)

                # embed.title = "Server Invite Deleted"
                # if invite.inviter:
                #     embed.set_author(name=str(invite.inviter), icon_url=invite.inviter.avatar_url)

                #     embed.set_footer(text=f"ID: {invite.inviter.id}")
                # embed.description = f"An invite for {getattr(invite.channel , 'mention', 'deleted-channel')} was just deleted. It was created {human_timedelta(IST.localize(invite.created_at))}"
                # embed.add_field(name="Uses", value=f"{invite.uses} times")

                # return embed, channel

            else:

                embed.title = "Discord Invite Posted"

                embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
                embed.description = f"{message.author.mention} posted an [Invite link]({message.jump_url}) (`{invite.code}`) in {message.channel.mention} that leads to the server **{invite.guild.name}**"

                embed.set_footer(text=f"ID: {message.id}")

                return embed, channel

        elif _type == LogType.ping:
            message = kwargs.get("message")
            mentions = kwargs.get("mentions")

            check = await get_channel(_type, message.guild)
            if not check:
                return

            channel, color = check

            check = await check_permissions(_type, channel)
            if not check:
                return

            mentions = "\n- ".join(mentions)
            embed.color = discord.Color(color)
            embed.title = "Ping Logs"
            embed.set_footer(text="ID: {0}".format(message.id), icon_url=self.bot.user.avatar_url)
            embed.set_author(name=message.author, icon_url=message.author.avatar_url)
            embed.description = f"{message.author.mention} [mentioned]({message.jump_url}) the following in {message.channel.mention}:\n\n-{mentions}"
            return embed, channel

        elif _type == LogType.cmd:
            ctx = kwargs.get("ctx")

            check = await get_channel(_type, ctx.guild)
            if not check:
                return

            channel, color = check

            check = await check_permissions(_type, channel)
            if not check:
                return

            if ctx.command.description:
                description = f"{ctx.command.description}\n\n{ctx.command.help}"
            else:
                description = ctx.command.help or "No help found..."

            embed.color = discord.Color(color)
            embed.title = "Command Used"
            embed.set_footer(text="ID: {0}".format(ctx.message.id))
            embed.description = f"{ctx.author.mention} used [{ctx.command.qualified_name}]({ctx.message.jump_url}) in {ctx.channel.mention}"
            embed.add_field(name="Command Description:", value=description)
            return embed, channel

        elif _type == LogType.voice:
            member = kwargs.get("member")
            before = kwargs.get("before")
            after = kwargs.get("after")

            check = await get_channel(_type, member.guild)
            if not check:
                return

            channel, color = check

            check = await check_permissions(_type, channel)
            if not check:
                return

            embed.color = discord.Color(color)
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            embed.set_footer(text=f"ID: {member.id}", icon_url=member.avatar_url)

            if before.channel != after.channel:
                if not before.channel:
                    embed.title = "Member joined a VC"
                    embed.description = f"{member.mention} joined {after.channel.mention}"
                    self.vc[member.id] = datetime.now(tz=IST)

                elif not after.channel:
                    embed.title = "Member left a VC"

                    embed.description = f"{member.mention} left {before.channel.mention}"

                    if not member.bot:
                        try:
                            t = datetime.now(tz=IST) - self.vc[member.id]
                            self.vc.pop(member.id)
                            embed.description += f"\nThey were in vc for {humanize.precisedelta(t)}"
                        except KeyError:
                            pass

                else:
                    embed.title = "Member switched VC"
                    embed.description = (
                        f"{member.mention} switched from {before.channel.mention} to {after.channel.mention}"
                    )

                    if not member.bot:
                        try:
                            t = datetime.now(tz=IST) - self.vc[member.id]
                            self.vc[member.id] = datetime.now(tz=IST)
                            embed.description = f"\nThere were in {before.channel.mention} for {humanize.precisedelta(t)}"
                        except:
                            pass
                return embed, channel

        elif _type == LogType.role:
            subtype = kwargs.get("subtype")
            role = kwargs.get("role")

            check = await get_channel(_type, role.guild)
            if not check:
                return

            channel, color = check

            check = await check_permissions(_type, channel)
            if not check:
                return

            embed.color = discord.Color(color)
            embed.set_footer(text=f"ID: {role.id}", icon_url=self.bot.user.avatar_url)

            if subtype == "create":
                embed.title = "New Role Created"
                color = "#{:06x}".format(role.color.value)
                embed.description = f"{role.mention} was just created.\n**Color:** {color}\n**Mentionable:** {role.mentionable}\n**Displayed separately:** {role.hoist}"

                return embed, channel

            if subtype == "delete":
                embed.title = "Role was deleted"
                color = "#{:06x}".format(role.color.value)
                embed.description = (
                    f"'**{role.name}**' was deleted. It was created {human_timedelta(IST.localize(role.created_at) + timedelta(hours=5, minutes=30))}"
                    f"\n**Color:** {color}\n**Mentionable:** {role.mentionable}\n**Position:** {role.position}"
                )
                return embed, channel
            before = kwargs.get("before")

            before_r = {
                "Name": before.name,
                "Color": "#{:06x}".format(before.color.value),
                "Separated": before.hoist,
                "Mentionable": before.mentionable,
                "Position": before.position,
            }
            after_r = {
                "Name": role.name,
                "Color": "#{:06x}".format(role.color.value),
                "Separated": role.hoist,
                "Mentionable": role.mentionable,
                "Position": role.position,
            }

            diff = [k for k in before_r if before_r[k] != after_r[k]]
            b_text = ""
            for i in diff:
                b_text += f"**{i}:** {before_r.get(i)}\n"

            a_text = ""
            for i in diff:
                a_text += f"**{i}:** {after_r.get(i)}\n"

            added_perms = set()
            removed_perms = set()
            for p, v in before.permissions:
                if not v and getattr(role.permissions, p):
                    added_perms.add(p)

                elif v and not getattr(role.permissions, p):
                    removed_perms.add(p)

            embed.title = "Role was Updated"
            embed.set_footer(text=f"ID: {before.id}", icon_url=self.bot.user.avatar_url)
            embed.add_field(name="Before", value=b_text)
            embed.add_field(name="After", value=a_text)
            embed.add_field(
                name="Permissions",
                value=f"**Added:** {', '.join(added_perms)}\n**Removed:** {' '.join(removed_perms)}",
            )
            return embed, channel
