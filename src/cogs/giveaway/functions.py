from core import Context
import discord


async def create_giveaway(ctx: Context):
    pass


async def gembed(ctx: Context, value: int, description: str):
    embed = discord.Embed(color=ctx.bot.color, title=f"🎉 Giveaway Setup ({value}/6)")
    embed.description = description
    embed.set_footer(text=f'Reply with "cancel" to stop the process.', icon_url=ctx.bot.avatar_url)
    return await ctx.send(embed=embed, embed_perms=True)
