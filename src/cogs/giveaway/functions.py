from discord.ext.commands import Converter, CommandError
from contextlib import suppress
from models import Giveaway
from core import Context
import discord, config
import utils
import tortoise.exceptions
from utils.time import plural


class GiveawayConverter(Converter):
    async def convert(self, ctx, argument):
        try:
            argument = int(argument)
        except ValueError:
            pass

        try:
            return await Giveaway.get(message_id=argument)

        except tortoise.exceptions.DoesNotExist:
            pass

        raise GiveawayError(
            f"This is not a valid Message ID.\n\nUse `{ctx.prefix}glist` to get a list of all your running giveaways."
        )


class GiveawayError(CommandError):
    pass


async def create_giveaway(giveaway: Giveaway, **kwargs):
    current = kwargs.get("current")
    end_at = utils.human_timedelta(giveaway.end_at, suffix=False, brief=False, accuracy=2)
    channel = giveaway.channel

    msg = await channel.send(content="🎉 **GIVEAWAY** 🎉", embed=get_giveaway_embed(giveaway))
    await msg.add_reaction("🎉")

    if current:
        embed = discord.Embed(title="Giveaway Started!", color=config.COLOR)
        embed.description = (
            f"The giveaway for {giveaway.prize} has been created in {channel.mention} and will last for {end_at}."
            f"\n[Click me to Jump there!]({msg.jump_url})"
        )
        await current.send(embed=embed)

    return msg


async def gembed(ctx: Context, value: int, description: str):
    embed = discord.Embed(color=ctx.bot.color, title=f"🎉 Giveaway Setup • ({value}/6)")
    embed.description = description
    embed.set_footer(text=f'Reply with "cancel" to stop the process.', icon_url=ctx.bot.user.avatar_url)
    return await ctx.send(embed=embed, embed_perms=True)


def get_giveaway_embed(giveaway: Giveaway):

    host = getattr(giveaway.host, "mention", "`Not Found!`")
    end_at = utils.human_timedelta(giveaway.end_at, suffix=False, brief=False, accuracy=2)

    embed = discord.Embed(title=f"🎁 {giveaway.prize}", color=config.COLOR, timestamp=giveaway.end_at)
    embed.description = "React with 🎉 to enter!\n" f"Hosted by: {host}\n" f"Remaining Time: {end_at}\n\n"

    if giveaway.required_msg:
        embed.description += f"📣 Must have **{giveaway.required_msg} messages** to enter!\n"

    if giveaway.required_role_id:
        embed.description += f"📣 Must have {giveaway.req_role.mention} role to enter!"

    embed.set_footer(text=f"{plural(giveaway.winners):winner|winners} | Ends at")

    return embed


async def check_giveaway_requirements(giveaway: Giveaway):
    pass


async def refresh_giveaway(giveaway: Giveaway):
    embed = get_giveaway_embed(giveaway)
    channel = giveaway.channel

    if not channel:
        await Giveaway.filter(pk=giveaway.id).delete()

    msg = await channel.fetch_message(giveaway.message_id)
    if not msg:
        await Giveaway.filter(pk=giveaway.id).delete()

    with suppress(discord.Forbidden, discord.HTTPException):
        await msg.edit(embed=embed)
