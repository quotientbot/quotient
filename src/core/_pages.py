from contextlib import suppress

from utils.default import split_list
from .Context import Context

import typing as T

import discord

from .views import QuotientView
import asyncio


class PageLine(T.NamedTuple):
    line: str = None
    image: str = None


class QuoPages:
    def __init__(
        self,
        ctx: Context,
        *,
        per_page=10,
        timeout=60.0,
        title=None,
        show_page_count=True,
        embed_color=0x00FFB3,
    ):

        self.ctx = ctx

        self.per_page = per_page
        self.timeout = timeout
        self.title = title or discord.Embed.Empty
        self.show_page_count = show_page_count

        self.enteries: T.List[PageLine] = []

        self.items: T.List[discord.ui.Item] = []
        self.embed_color = embed_color

        self.pages = []

        self.cur_page = 1

    def add_line(self, line: PageLine):
        self.enteries.append(line)

    @property
    def embed(self) -> discord.Embed:
        _p = self.pages[self.cur_page - 1]

        _e = discord.Embed(color=self.embed_color, title=self.title)
        _e.description = _p.line
        if _p.image:
            _e.set_image(url=_e.image)

        if self.show_page_count:
            _e.set_footer(text=f"Page {self.pages.index(_p) + 1} of {len(self.pages)}")
        return _e

    @property
    def current_page(self):
        ...

    async def paginate(self):
        if not self.per_page > 1:
            self.pages = self.enteries

        else:
            for _ in split_list(self.enteries, self.per_page):
                _: T.List[PageLine]
                self.pages.append(PageLine("".join(ent.line for ent in _), _[0].image))

        view = None
        if self.items:
            view = QuotientView(self.ctx)
            for _ in self.items:
                view.add_item(_)

        if not len(self.pages) > 1:
            view.message = await self.ctx.send(embed=self.embed, view=view)
            return


class QuoPageView(QuotientView):
    def __init__(self, ctx: Context, *, pages: T.List[PageLine], items: T.Optional[T.List[discord.ui.Item]] = None):
        super().__init__(ctx, timeout=40)

        self.pages = pages
        self.items = items
        self.current_page = 1

        __input_lock = asyncio.Lock()

        self.clear_items()

        self.fill_items()

    def fill_items(self):
        ...

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="first", emoji="<:double_left:878668594530099220>")
    async def first_page(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="previous", emoji="<:left:878668491660623872>")
    async def previous_page(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="skipto", label="Skip to page ...")
    async def skip_page(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="next", emoji="<:right:878668370331983913>")
    async def next_page(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="last", emoji="<:double_right:878668437193359392>")
    async def last_page(self, button: discord.Button, interaction: discord.Interaction):
        ...
