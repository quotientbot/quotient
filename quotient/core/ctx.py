from __future__ import annotations

import typing as T

import discord
from discord.ext import commands

if T.TYPE_CHECKING:
    from .bot import Quotient


class Context(commands.Context):
    bot: Quotient

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
