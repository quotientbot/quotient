from difflib import get_close_matches
import discord, io

from core.Context import Context


class TabularData:
    def __init__(self):
        self._widths = []
        self._columns = []
        self._rows = []

    def set_columns(self, columns):
        self._columns = columns
        self._widths = [len(c) + 2 for c in columns]

    def add_row(self, row):
        rows = [str(r) for r in row]
        self._rows.append(rows)
        for index, element in enumerate(rows):
            width = len(element) + 2
            if width > self._widths[index]:
                self._widths[index] = width

    def add_rows(self, rows):
        for row in rows:
            self.add_row(row)

    def render(self):
        """Renders a table in rST format.
        Example:
        +-------+-----+
        | Name  | Age |
        +-------+-----+
        | Alice | 24  |
        |  Bob  | 19  |
        +-------+-----+
        """

        sep = "+".join("-" * w for w in self._widths)
        sep = f"+{sep}+"

        to_draw = [sep]

        def get_entry(d):
            elem = "|".join(f"{e:^{self._widths[i]}}" for i, e in enumerate(d))
            return f"|{elem}|"

        to_draw.append(get_entry(self._columns))
        to_draw.append(sep)

        for row in self._rows:
            to_draw.append(get_entry(row))

        to_draw.append(sep)
        return "\n".join(to_draw)


async def tabulate_query(ctx, query, *args):
    records = await ctx.db.fetch(query, *args)

    if len(records) == 0:
        return await ctx.send("No results found.")

    headers = list(records[0].keys())
    table = TabularData()
    table.set_columns(headers)
    table.add_rows(list(r.values()) for r in records)
    render = table.render()

    fmt = f"```\n{render}\n```"
    if len(fmt) > 2000:
        fp = io.BytesIO(fmt.encode("utf-8"))
        await ctx.send("Too many results...", file=discord.File(fp, "results.txt"))
    else:
        await ctx.send(fmt)


async def member_msg_stats(ctx: Context, member):
    embed = ctx.bot.embed(ctx)


async def guild_msg_stats(ctx):
    pass


# async def find_query(ctx, query):
#     record = await FAQ.filter(aliases__icontains=query).all().first()
#     if record:
#         return record

#     return "\n".join(get_close_matches(query, (faq.aliases for faq in await FAQ.all())))
