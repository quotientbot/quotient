from datetime import datetime, timedelta
from core import Quotient, Cog, Context
from discord.utils import escape_markdown
from utils import IST, LogType
from models import Snipes
from .functions import *
import discord

__all__ = ("LoggingEvents",)

# TODO: fix if action done by the user themself
# TODO: fix if attachment isn't an image
class LoggingEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
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

    @Cog.listener()
    async def on_log(self, _type: LogType, **kwargs):

        print(_type)
        embed, channel = await self.handle_event(_type, **kwargs)

        if embed is not None and channel is not None:
            await channel.send(embed=embed)

    async def handle_event(self, _type: LogType, **kwargs):
        embed = discord.Embed()

        if _type == LogType.msg:
            subtype = kwargs.get("subtype")
            message = kwargs.get("message")

            check = await check_permissions(message.guild)
            if not check:
                return

            channel, color = await get_channel(_type, message.guild)
            if not channel:
                return

            if subtype == "single":
                audit_log_entry = await audit_entry(message.guild, discord.AuditLogAction.message_delete)

                deleted_by = (
                    f"{message.author.mention}"
                    if audit_log_entry.user.id == message.author.id
                    else f"{audit_log_entry.user.mention}"
                )

                embed.color = discord.Color(color)
                embed.timestamp = datetime.utcnow()
                embed.set_footer(text="DELETED", icon_url=self.bot.user.avatar_url)

                embed.description = (
                    f"Message sent by {message.author.mention} deleted in {message.channel.mention} by {deleted_by}."
                )
                embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)

                cont = escape_markdown(message.content)

                embed.add_field(name="Message:", value=cont, inline=False)

                if message.attachments:
                    embed.set_image(url=message.attachments[0].proxy_url)

                return embed, channel

            elif subtype == "bulk":
                message = message[0]
                audit_log_entry = await self.audit_entry(message.guild, discord.AuditLogAction.message_bulk_delete)
                deleted_by = (
                    f"{message.author.mention}"
                    if audit_log_entry.user.id == message.author.id
                    else f"{audit_log_entry.user.mention}"
                )

                msg_str = "------------------------------------------------------\n"

                for msg in message:
                    msg_str += f"Channel: {msg.channel.name}\nAuthor: {str(msg.author)}\nContent: {msg.content}\n------------------------------------------------------\n"

                embed.color = discord.Color(color)
                embed.description = f"🚮 Bulk messages deleted in {message.channel.mention} by {deleted_by}."
                embed.add_field(
                    name="Deleted message content:",
                    value=f"[Click Here to see deleted messages]({str(await self.bot.binclient.post(msg_str))})",
                    inline=False,
                )
                embed.set_footer(text="DELETED", icon_url=self.bot.user.avatar_url)
                embed.set_author(name=str(deleted_by.user), icon_url=deleted_by.user.avatar_url)
                embed.timestamp = datetime.utcnow()

                return embed, channel

            else:
                # edited msg
                pass
