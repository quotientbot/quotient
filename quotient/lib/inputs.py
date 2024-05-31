import asyncio

import discord
from discord.ext.commands import Context, TextChannelConverter

from .time import convert_to_seconds


class InputError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


async def text_channel_input(
    ctx: Context,
    check=None,
    timeout=120,
    delete_after=False,
    check_perms=True,
):
    check = check or (lambda m: m.channel == ctx.channel and m.author == ctx.author)
    try:
        message: discord.Message = await ctx.bot.wait_for(
            "message", check=check, timeout=timeout
        )
    except asyncio.TimeoutError:
        raise InputError("You failed to select a channel in time. Try again!")

    else:
        channel = await TextChannelConverter().convert(ctx, message.content)

        perms = channel.permissions_for(ctx.me)

        if not all((perms.read_messages, perms.send_messages, perms.embed_links)):
            raise InputError(
                f"Please make sure I have the following perms in {channel.mention}:\n"
                "`read_messages`,`send_messages`,`embed_links`."
            )

        if check_perms:
            if not all(
                (
                    perms.manage_channels,
                    perms.add_reactions,
                    perms.use_external_emojis,
                    perms.manage_permissions,
                    perms.manage_messages,
                )
            ):
                raise InputError(
                    f"Please make sure I have the following perms in {channel.mention}:\n"
                    "- `add reactions`\n- `use external emojis`\n- `manage channel`\n- `manage permissions`\n"
                    "- `manage messages`"
                )
        if delete_after:
            await message.delete(delay=0)

        return channel


async def simple_time_input(ctx: Context, timeout=120, delete_after=False) -> int:

    try:
        message: discord.Message = await ctx.bot.wait_for(
            "message",
            check=lambda x: x.channel.id == ctx.channel.id
            and x.author.id == ctx.author.id,
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        raise InputError("You failed to select a time in time. Try again!")

    else:
        if delete_after:
            await message.delete(delay=0)

        return convert_to_seconds(message.content)
