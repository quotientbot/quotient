from contextlib import suppress

from models import Autoevent
from utils import IST
from constants import EventType
from datetime import datetime
from core import Context
import discord


async def insert_or_update_config(ctx: Context, _type: EventType, channel: discord.TextChannel):
    guild = ctx.guild

    try:
        hook = await channel.create_webhook(
            name="Quotient",
            reason=f"[{ctx.author}] created the webhook for auto{_type.value}!",
            avatar=await ctx.me.avatar_url.read(),
        )

    except (discord.Forbidden, discord.HTTPException):
        return await ctx.error(f"Webhook limit reached. Couldn't create more webhooks in that channel.")

    # if everything goes right,

    else:
        record = await Autoevent.filter(guild_id=guild.id, type=_type).first()
        future = datetime.now(tz=IST)

        if not record:
            await Autoevent.create(
                guild_id=guild.id, type=_type, channel_id=channel.id, webhook=hook.url, send_time=future
            )

        else:
            # Try to delete webhooks at first....
            try:
                webhook = discord.Webhook.from_url(
                    record.webhook,
                    adapter=discord.AsyncWebhookAdapter(ctx.bot.session),
                )
                await webhook.delete()
            except:
                pass

            await Autoevent.filter(guild_id=guild.id, type=_type).update(
                channel_id=channel.id, webhook=hook.url, toggle=True, interval=30, send_time=future
            )

        return record


async def deliver_webhook(webhook, embed, _type, avatar):
    with suppress(discord.HTTPException, discord.NotFound, discord.Forbidden):
        await webhook.send(
            embed=embed,
            username=f"Quotient | Auto{_type.value}",
            avatar_url=avatar,
        )
