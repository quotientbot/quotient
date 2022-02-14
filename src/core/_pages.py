from contextlib import suppress
from .Context import Context

from typing import Tuple, Union, List
import discord


class QuoPages:
    def __init__(
        self,
        ctx: Context,
        *,
        per_page=10,
        timeout=60.0,
        title=None,
        show_page_count=True,
        items: List[discord.ui.Item] = [],
        embed_color=0x00FFB3
    ):

        self.ctx = ctx

        self.per_page = per_page
        self.timeout = timeout
        self.title = title
        self.show_page_count = show_page_count

        self.lines: List[Tuple[str, Union[None, str]]] = []

        self.items = items
        self.embed_color = embed_color

        self.cur_page = 1

    def add_line(self, line: Tuple[str, Union[None, str]]):
        self.lines.append(line)

    @property
    def embed(self) -> discord.Embed:

        _e = discord.Embed(color=self.embed_color)
