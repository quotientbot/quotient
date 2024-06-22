import discord
from discord.ext import commands
from PIL import ImageColor


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
