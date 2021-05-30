from discord.ext import commands
from core import Context
from models import Tag


class TagName(commands.clean_content):
    def __init__(self, *, lower=False):
        self.lower = lower
        super().__init__()

    async def convert(self, ctx, argument):
        converted = await super().convert(ctx, argument)
        lower = converted.lower().strip()

        if not lower:
            raise commands.BadArgument("Missing tag name.")

        if len(lower) > 100:
            raise commands.BadArgument("Tag name is a maximum of 100 characters.")

        first_word, _, _ = lower.partition(" ")

        root = ctx.bot.get_command("tag")
        if first_word in root.all_commands:
            raise commands.BadArgument("This tag name starts with a reserved word.")

        return converted if not self.lower else lower


class TagConverter(commands.Converter):
    pass


async def create_tag(ctx: Context, name: str, content: str, is_embed=False, is_nsfw=False):

    query = "SELECT * FROM tags WHERE name = $1 AND guild_id = $2"
    record = await ctx.bot.db.fetchrow(query, name, ctx.guild.id)

    if record is None:

        await Tag.create(
            guild_id=ctx.guild.id,
            name=name,
            content=(str(content).replace("'", '"')),
            owner_id=ctx.author.id,
            is_nsfw=is_nsfw,
            is_embed=is_embed,
        )
        return await ctx.success("ban gya")

    await ctx.error("pehle se bana hai")


async def is_valid_name(ctx: Context, name: str) -> bool:
    tag = await Tag.get_or_none(name=name, guild_id=ctx.guild.id)

    if tag:
        return False
    else:
        return True


async def increment_usage(ctx: Context, name) -> None:
    query = "UPDATE tags SET usage = usage + 1 WHERE guild_id = $1 AND name = $2"
    await ctx.db.execute(query, ctx.guild.id, name)
