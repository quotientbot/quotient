from contextlib import suppress
from typing import NamedTuple, Optional

import discord

from .default import get_chunks


class Page(NamedTuple):
    index: int
    content: str


class Pages:
    def __init__(self, pages: list):
        self.pages = pages
        self.cur_page = 1

    @property
    def current_page(self) -> Page:
        return Page(self.cur_page, self.pages[self.cur_page - 1])

    @property
    def next_page(self) -> Optional[Page]:
        if self.cur_page == self.total:
            return None

        self.cur_page += 1
        return self.current_page

    @property
    def previous_page(self) -> Optional[Page]:
        if self.cur_page == 1:
            return None

        self.cur_page -= 1
        return self.current_page

    @property
    def first_page(self) -> Page:
        self.cur_page = 1
        return self.current_page

    @property
    def last_page(self) -> Page:
        self.cur_page = self.total
        return self.current_page

    @property
    def total(self):
        return len(self.pages)


class QuoPaginator:
    def __init__(self, ctx, *, per_page=10, timeout=60.0, title=None, show_page_count=True):
        self.ctx = ctx
        self.per_page = per_page
        self.timeout = timeout
        self.title = title
        self.show_page_count = show_page_count

        self.lines = []
        self.pages = None

    def add_line(self, line: str, sep="\n"):
        self.lines.append(f"{line}{sep}")

    @property
    def embed(self):
        page = self.pages.current_page

        e = discord.Embed(color=self.ctx.bot.color)
        if self.title:
            e.title = self.title

        e.description = page.content

        if self.show_page_count:
            e.set_footer(text=f"Page {page.index} of {self.pages.total}")

        return e

    async def start(self):
        _pages = []
        for page in get_chunks(self.lines, self.per_page):
            _pages.append("".join(page))

        self.pages = Pages(_pages)

        if not self.pages.total > 1:
            return await self.ctx.send(embed=self.embed)

        view = PaginatorView(
            self.ctx, pages=self.pages, embed=self.embed, timeout=self.timeout, show_page_count=self.show_page_count
        )
        view.message = await self.ctx.send(embed=self.embed, view=view)


class PaginatorView(discord.ui.View):
    message: discord.Message

    def __init__(self, ctx, pages: Pages, embed, timeout, show_page_count):

        super().__init__(timeout=timeout)

        self.ctx = ctx
        self.pages = pages
        self.embed: discord.Embed = embed
        self.show_page_count = show_page_count

        if self.pages.cur_page == 1:
            self.children[0].disabled = True
            self.children[1].disabled = True

    def lock_bro(self):

        if self.pages.cur_page == self.pages.total:
            self.children[0].disabled = False
            self.children[1].disabled = False

            self.children[2].disabled = True
            self.children[3].disabled = True

        elif self.pages.cur_page == 1:
            self.children[0].disabled = True
            self.children[1].disabled = True

            self.children[2].disabled = False
            self.children[3].disabled = False

        elif 1 < self.pages.cur_page < self.pages.total:
            for b in self.children:
                b.disabled = False

    def update_embed(self, page: Page):
        if self.show_page_count:
            self.embed.set_footer(text=f"Page {page.index} of {self.pages.total}")

        self.embed.description = page.content

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "Sorry, you can't use this interaction as it is not started by you.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:

        for b in self.children:
            b.style, b.disabled = discord.ButtonStyle.grey, True

        with suppress(discord.HTTPException):
            await self.message.edit(view=self)

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="first", emoji="<:double_left:878668594530099220>")
    async def first(self, button: discord.ui.Button, interaction: discord.Interaction):
        page = self.pages.first_page

        self.update_embed(page)
        self.lock_bro()
        await interaction.message.edit(embed=self.embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="previous", emoji="<:left:878668491660623872>")
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        page = self.pages.previous_page
        self.update_embed(page)
        self.lock_bro()
        await interaction.message.edit(embed=self.embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="next", emoji="<:right:878668370331983913>")
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        page = self.pages.next_page
        self.update_embed(page)

        self.lock_bro()
        await interaction.message.edit(embed=self.embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="last", emoji="<:double_right:878668437193359392>")
    async def last(self, button: discord.ui.Button, interaction: discord.Interaction):
        page = self.pages.last_page

        self.update_embed(page)
        self.lock_bro()
        await interaction.message.edit(embed=self.embed, view=self)
