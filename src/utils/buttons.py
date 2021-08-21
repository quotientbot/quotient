from typing import NamedTuple
from enum import Enum
import discord


class LinkType(NamedTuple):
    name: str
    url: str


class LinkButton(discord.ui.View):
    def __init__(self, links: list):
        super().__init__()

        for link in links:
            self.add_item(discord.ui.Button(label=link.name, url=link.url))
