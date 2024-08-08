import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from typing import Callable

import discord
from discord.ext import commands
from PIL import ImageColor


class to_async:
    def __init__(self):
        self.executor = ThreadPoolExecutor()

    def __call__(self, blocking: Callable):
        @wraps(blocking)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_running_loop()
            func = partial(blocking, *args, **kwargs)
            return await loop.run_in_executor(self.executor, func)

        return wrapper


class Snowflake:
    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str) -> int:
        try:
            return int(argument)
        except ValueError:
            param = ctx.current_parameter
            if param:
                raise commands.BadArgument(f"{param.name} argument expected a Discord ID not {argument!r}")
            raise commands.BadArgument(f"expected a Discord ID not {argument!r}")


class ColorConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str) -> discord.Color:

        named_color = self._parse_named_color(arg)
        if named_color:
            return discord.Color.from_rgb(*named_color)

        discord_color = await self._parse_discord_color(ctx, arg)
        if discord_color:
            return discord_color

        raise commands.BadColorArgument(f"Could not convert '{arg}' to a valid color.")

    def _parse_named_color(self, arg: str) -> tuple[int, int, int] | None:
        try:
            return ImageColor.getrgb(arg.lower())
        except ValueError:
            return None

    async def _parse_discord_color(self, ctx: commands.Context, arg: str) -> discord.Color | None:
        color_converter = commands.ColorConverter()
        try:
            return await color_converter.convert(ctx, arg)
        except commands.BadColorArgument:
            return None
