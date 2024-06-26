import os

import discord

from .emojis import CROSS


async def send_simple_embed(channel: discord.TextChannel, description: str, delete_after: float = None) -> discord.Message:
    return await channel.send(
        embed=discord.Embed(color=int(os.getenv("DEFAULT_COLOR")), description=description), delete_after=delete_after
    )


async def send_error_embed(
    channel: discord.TextChannel, description: str, delete_after: float = None, image_url: str = None
) -> discord.Message:
    return await channel.send(
        embed=discord.Embed(color=discord.Color.red(), description=CROSS + " | " + description).set_image(url=image_url),
        delete_after=delete_after,
    )


def truncate_string(value: str, max_length=128, suffix="...") -> str:
    """
    Truncate a string to a certain length and add a suffix if it exceeds the length.
    """
    string_value = str(value)
    string_truncated = string_value[: min(len(string_value), (max_length - len(suffix)))]
    suffix = suffix if len(string_value) > max_length else ""
    return string_truncated + suffix


class plural:
    def __init__(self, value: int | list):
        self.value = value

        if isinstance(self.value, list):
            self.value = len(self.value)

    def __format__(self, format_spec: str):
        v = self.value
        singular, sep, plural = format_spec.partition("|")

        plural = plural or f"{singular}s"
        if abs(v) != 1:
            return f"{v} {plural}"
        return f"{v} {singular}"
