import asyncio
from datetime import datetime

import discord
from discord.ext.commands import Context, RoleConverter, TextChannelConverter

from .time import convert_to_seconds, parse_natural_time


class InputError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


async def text_input(ctx: Context, check=None, timeout=120, delete_after=False) -> str:
    check = check or (lambda m: m.channel == ctx.channel and m.author == ctx.author)
    try:
        message: discord.Message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        raise InputError("You failed to input in time. Try again!")

    else:
        if delete_after:
            await message.delete(delay=0)

        return message.content


async def text_channel_input(
    ctx: Context,
    check=None,
    timeout=120,
    delete_after=False,
    check_perms=True,
):
    check = check or (lambda m: m.channel == ctx.channel and m.author == ctx.author)
    try:
        message: discord.Message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        raise InputError("You failed to select a channel in time. Try again!")

    else:
        channel = await TextChannelConverter().convert(ctx, message.content)

        perms = channel.permissions_for(ctx.me)

        if not all((perms.read_messages, perms.send_messages, perms.embed_links)):
            raise InputError(
                f"Please make sure I have the following perms in {channel.mention}:\n" "`read_messages`,`send_messages`,`embed_links`."
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


async def guild_role_input(ctx: Context, check=None, timeout=120, delete_after=False) -> discord.Role:
    check = check or (lambda m: m.channel == ctx.channel and m.author == ctx.author)
    try:
        message: discord.Message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        raise InputError("You failed to select a role in time. Try again!")

    else:
        role = await RoleConverter().convert(ctx, message.content)

        if delete_after:
            await message.delete(delay=0)

        return role


async def simple_time_input(ctx: Context, timeout=120, delete_after=False) -> int:

    try:
        message: discord.Message = await ctx.bot.wait_for(
            "message",
            check=lambda x: x.channel.id == ctx.channel.id and x.author.id == ctx.author.id,
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        raise InputError("You failed to select a time in time. Try again!")

    else:
        if delete_after:
            await message.delete(delay=0)

        return convert_to_seconds(message.content)


class InputModal(discord.ui.Modal):
    def __init__(self, title: str, timeout: float):
        super().__init__(title=title, timeout=timeout)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()


async def integer_input_modal(
    inter: discord.Interaction,
    title: str = "Enter an integer",
    label: str = "Input here",
    placeholder: str = None,
    default: str = None,
    timeout: float = 120,
) -> int | None:

    v = InputModal(title=title, timeout=timeout)
    v.add_item(discord.ui.TextInput(label=label, placeholder=placeholder, max_length=5, min_length=1, default=default))

    await inter.response.send_modal(v)

    await v.wait()

    if v.children[0].value is None:
        return None

    try:
        return int(v.children[0].value)
    except ValueError:
        return None


async def time_input_modal(
    inter: discord.Interaction,
    title: str = "Enter a time",
    label: str = "Input here",
    default: str = None,
) -> datetime | None:

    v = InputModal(title=title, timeout=120)
    v.add_item(
        discord.ui.TextInput(label=label, max_length=8, min_length=3, default=default, placeholder="Ex: 10AM, 10:14PM, 22:00, etc")
    )

    await inter.response.send_modal(v)

    await v.wait()

    if v.children[0].value is None:
        return None

    try:
        return parse_natural_time(v.children[0].value)
    except (TypeError, ValueError):
        return None
