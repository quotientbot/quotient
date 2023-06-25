from __future__ import annotations

import asyncio
import typing as T

import discord

from utils.default import split_list

from .Context import Context
from .views import QuotientView


class PageLine(T.NamedTuple):
    line: T.Optional[str] = None
    image: T.Optional[str] = None
    # embed: T.Optional[discord.Embed] = None


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
        compact=False,
    ):

        self.ctx = ctx

        self.per_page = per_page
        self.timeout = timeout
        self.title = title or None
        self.show_page_count = show_page_count

        self.enteries: T.List[PageLine] = []

        self.items: T.List[discord.ui.Item] = []
        self.embed_color = embed_color

        self.compact = compact

        self.pages: T.List[PageLine] = []

        self.cur_page = 1

    def add_line(self, line: PageLine):
        self.enteries.append(line)

    @property
    def embed(self) -> discord.Embed:
        _p = self.pages[self.cur_page - 1]

        _e = discord.Embed(color=self.embed_color, title=self.title)
        _e.description = _p.line
        if _p.image:
            _e.set_image(url=_p.image)

        if self.show_page_count:
            _e.set_footer(text=f"Page {self.pages.index(_p) + 1} of {len(self.pages)}")
        return _e

    @property
    def current_page(self):
        ...

    async def paginate(self):
        if self.per_page <= 1:
            self.pages = self.enteries

        else:
            for _ in split_list(self.enteries, self.per_page):
                _: T.List[PageLine]
                self.pages.append(PageLine("".join(ent.line for ent in _), _[0].image))

        view = QuoPageView(
            self.ctx,
            pages=self.pages,
            items=self.items,
            embed=self.embed,
            show_count=self.show_page_count,
            need_skip=self.compact,
        )
        if len(self.pages) <= 1:
            view.message = await self.ctx.send(embed=self.embed)
            return

        view.message = await self.ctx.send(embed=self.embed, view=view)


class QuoPageView(QuotientView):
    def __init__(
        self,
        ctx: Context,
        *,
        pages: T.List[PageLine],
        items: T.Optional[T.List[discord.ui.Item]] = None,
        embed: discord.Embed,
        show_count: bool,
        need_skip: bool,
    ):
        super().__init__(ctx, timeout=40)

        self.pages = pages
        self.items = items
        self.current_page = 1
        self.embed = embed
        self.show_count = show_count
        self.need_skip = need_skip

        self.__input_lock = asyncio.Lock()

        self.clear_items()
        self.fill_items()

    def fill_items(self) -> None:
        for item in self.items:  # Not sure about these item's positions
            self.add_item(item)

        self.add_item(self.first_page)
        self.add_item(self.previous_page)

        if self.need_skip:
            self.add_item(self.skip_page)

        self.add_item(self.next_page)
        self.add_item(self.last_page)

    def update_embed(self):
        if self.show_count:
            self.embed.set_footer(text=f"Page {self.current_page} of {len(self.pages)}")

        self.embed.description = self.pages[self.current_page - 1].line

        if self.pages[self.current_page - 1].image:
            self.embed.set_image(url=self.pages[self.current_page - 1].image)

    @discord.ui.button(
        style=discord.ButtonStyle.green,
        custom_id="first",
        emoji="<:double_left:878668594530099220>",
    )
    async def first_page(self, interaction: discord.Interaction, button: discord.Button):
        self.current_page = 1
        self.update_embed()

        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(
        style=discord.ButtonStyle.green, custom_id="previous", emoji="<:left:878668491660623872>"
    )
    async def previous_page(self, interaction: discord.Interaction, button: discord.Button):
        if self.current_page == 1:
            return

        self.current_page -= 1
        self.update_embed()

        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(
        style=discord.ButtonStyle.green, custom_id="skipto", label="Skip to page ..."
    )
    async def skip_page(self, interaction: discord.Interaction, button: discord.Button):
        if self.__input_lock.locked():
            return await interaction.response.send_message(
                "Already waiting for your response...", ephemeral=True
            )

        if self.message is None:
            return

        async with self.__input_lock:
            channel = self.message.channel
            author_id = interaction.user and interaction.user.id
            await interaction.response.send_message(
                "Please enter the page number you want to skip to.", ephemeral=True
            )

            def _msg_check(m: discord.Message) -> bool:
                return m.author.id == author_id and channel == m.channel and m.content.isdigit()

            try:
                msg = await self.ctx.bot.wait_for("message", check=_msg_check, timeout=30.0)
            except asyncio.TimeoutError:
                await interaction.followup.send("Took too long.", ephemeral=True)
                await asyncio.sleep(5)
            else:
                page = int(msg.content)
                await msg.delete()

                if page > len(self.pages):
                    await interaction.followup.send("Page number too high.", ephemeral=True)
                    return

                self.current_page = page
                self.update_embed()

                if interaction.response.is_done():
                    if self.message:
                        await self.message.edit(embed=self.embed, view=self)
                else:
                    await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(
        style=discord.ButtonStyle.green, custom_id="next", emoji="<:right:878668370331983913>"
    )
    async def next_page(self, interaction: discord.Interaction, button: discord.Button):
        if self.current_page == len(self.pages):
            return

        self.current_page += 1
        self.update_embed()

        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(
        style=discord.ButtonStyle.green,
        custom_id="last",
        emoji="<:double_right:878668437193359392>",
    )
    async def last_page(self, interaction: discord.Interaction, button: discord.Button):
        self.current_page = len(self.pages)
        self.update_embed()

        await interaction.response.edit_message(embed=self.embed, view=self)
