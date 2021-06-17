from models import Giveaway
from datetime import timedelta
from core import Context
import discord, config
import utils
from utils.time import plural


async def create_giveaway(giveaway: Giveaway, **kwargs):
    current = kwargs.get("current")
    host = getattr(giveaway.host, "mention", "`Not Found!`")
    end_at = utils.human_timedelta(giveaway.end_at)
    channel = giveaway.channel

    embed = discord.Embed(title=f"🎁 {giveaway.prize}", color=config.COLOR, timestamp=giveaway.end_at)
    embed.description = "React with 🎉 to enter!\n" f"Hosted by: {host}\n" f"Remaining Time: {end_at}\n\n"

    if giveaway.required_msg:
        embed.description += f"📣 Must have **{giveaway.required_msg} messages** to enter!\n"

    if giveaway.required_role_id:
        embed.description += f"📣 Must have {giveaway.req_role.mention} role to enter!"

    embed.set_footer(text=f"{plural(giveaway.winners):winner|winners} | Ends at")

    msg = await channel.send(content="🎉 **GIVEAWAY** 🎉", embed=embed)
    await msg.add_reaction("🎉")

    if current:
        embed = discord.Embed(title="Giveaway Started!", color=config.COLOR)
        embed.description = (
            f"The giveaway for {giveaway.prize} has been created in {channel.mention} and will last for {end_at}"
            f"[Click me to Jump there!]({msg.jump_url})"
        )
        await current.send(embed=embed)

    return msg


async def gembed(ctx: Context, value: int, description: str):
    embed = discord.Embed(color=ctx.bot.color, title=f"🎉 Giveaway Setup • ({value}/6)")
    embed.description = description
    embed.set_footer(text=f'Reply with "cancel" to stop the process.', icon_url=ctx.bot.user.avatar_url)
    return await ctx.send(embed=embed, embed_perms=True)
