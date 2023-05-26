from discord.ext import commands

from core import Context
from models import Tag
from utils.converters import QuoMember


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
    async def convert(self, ctx, argument: str):
        try:
            argument = int(argument)
            tag = await Tag.get_or_none(id=argument, guild_id=ctx.guild.id)

        except ValueError:
            tag = await Tag.get_or_none(guild_id=ctx.guild.id, name=argument)

        if not tag:
            search = await Tag.filter(guild_id=ctx.guild.id, name__icontains=argument).limit(3)
            text = f"**{argument}** is not a valid Tag Name or ID."
            if search:
                tags = "\n".join((f"- {tag.name}" for tag in search))
                text += f"\n\nMaybe you were looking for:\n{tags}"
            raise commands.BadArgument(text)

        return tag


async def is_valid_name(ctx: Context, name: str) -> bool:
    tag = await Tag.get_or_none(name=name, guild_id=ctx.guild.id)

    return not tag


async def increment_usage(ctx: Context, name) -> None:
    query = "UPDATE tags SET usage = usage + 1 WHERE guild_id = $1 AND name = $2"
    await ctx.db.execute(query, ctx.guild.id, name)


def emojize(seq):
    emoji = 129351
    for index, value in enumerate(seq):
        yield chr(emoji + index), value


async def guild_tag_stats(ctx: Context):
    e = ctx.bot.embed(ctx, title="Tag Stats")
    e.set_footer(text="These statistics are server-specific.")

    records = await Tag.filter(guild_id=ctx.guild.id).all().order_by("-usage").only("id", "name", "usage").limit(3)

    if not records:
        e.description = "No tag statistics here."

    else:
        e.description = f"{len(records)} tags, {sum(t.usage for t in records)} tag uses"

    value = "\n".join(f"{emoji}: {tag.name} ({tag.usage} uses)" for (emoji, (tag)) in emojize(records))

    e.add_field(name="Top Tags", value=value, inline=False)

    query = """SELECT
                    COUNT(*) AS tag_uses,
                    user_id
                   FROM commands
                   WHERE guild_id=$1 AND cmd='tag'
                   GROUP BY user_id
                   ORDER BY COUNT(*) DESC
                   LIMIT 3;
                """

    records = await ctx.db.fetch(query, ctx.guild.id)

    if len(records) < 3:
        records.extend((None, None) for _ in range(3 - len(records)))

    value = "\n".join(
        f"{emoji}: <@{author_id}> ({uses} times)" if author_id else f"{emoji}: No one!"
        for (emoji, (uses, author_id)) in emojize(records)
    )

    e.add_field(name="Top Tag Users", value=value, inline=False)

    query = """SELECT
                       COUNT(*) AS "Tags",
                       owner_id
                   FROM tags
                   WHERE guild_id=$1
                   GROUP BY owner_id
                   ORDER BY COUNT(*) DESC
                   LIMIT 3;
                """
    # I don't think they made group_by clause in tortoise
    records = await ctx.db.fetch(query, ctx.guild.id)
    if not records:
        text = "No statistics to show here."
    else:
        value = "\n".join(f"{emoji}: <@{owner_id}> ({count} tags)" for (emoji, (count, owner_id)) in emojize(records))

    e.add_field(name="Top Tag Creators", value=value, inline=False)
    await ctx.send(embed=e, embed_perms=True)


async def member_tag_stats(ctx: Context, member: QuoMember):
    e = ctx.bot.embed(ctx)
    e.set_author(name=str(member), icon_url=member.display_avatar.url)

    e.set_footer(text="These statistics are server-specific.")

    query = """SELECT COUNT(*)
                   FROM commands
                   WHERE guild_id=$1 AND cmd='tag' AND user_id=$2
                """

    count = await ctx.db.fetchrow(query, ctx.guild.id, member.id)

    query = """SELECT
                    name,
                    usage,
                    COUNT(*) OVER() AS "Count",
                    SUM(usage) OVER () AS "Uses"
                FROM tags
                WHERE guild_id=$1 AND owner_id=$2
                ORDER BY usage DESC
                LIMIT 3;
                """

    records = await ctx.db.fetch(query, ctx.guild.id, member.id)

    if len(records) > 1:
        owned = records[0]["Count"]
        uses = records[0]["Uses"]
    else:
        owned = "None"
        uses = 0

    e.add_field(name="Owned Tags", value=owned)
    e.add_field(name="Owned Tag Uses", value=uses)
    e.add_field(name="Tag Command Uses", value=count[0])

    if len(records) < 3:
        records.extend((None, None, None, None) for _ in range(3 - len(records)))

    emoji = 129351

    for (offset, (name, uses, _, _)) in enumerate(records):
        value = f"{name} ({uses} uses)" if name else "Nothing!"
        e.add_field(name=f"{chr(emoji + offset)} Owned Tag", value=value)

    await ctx.send(embed=e, embed_perms=True)
