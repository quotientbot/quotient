import asyncio
import os
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


class ChannelSelectorInput(discord.ui.ChannelSelect):
    def __init__(self, placeholder: str = "Please select a channel ..."):
        super().__init__(placeholder=placeholder, channel_types=[discord.ChannelType.text])

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.stop()


class RoleSelectInput(discord.ui.RoleSelect):
    def __init__(self, placeholder: str = "Please select a role ..."):
        super().__init__(placeholder=placeholder)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.stop()


class UserSelectInput(discord.ui.UserSelect):
    def __init__(self, placeholder: str = "Please select a user ...", multiple: bool = False):
        super().__init__(placeholder=placeholder, max_values=1 if not multiple else 10)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.stop()


async def user_input(
    inter: discord.Interaction,
    message: str,
    placeholder: str = "Please select users (upto 10) ...",
    multiple: bool = True,
    delete_after=True,
) -> list[discord.Member] | None:

    v = discord.ui.View(timeout=180)
    v.add_item(UserSelectInput(placeholder=placeholder, multiple=multiple))

    m = await inter.followup.send(
        embed=discord.Embed(color=int(os.getenv("DEFAULT_COLOR")), description=message), view=v, ephemeral=True
    )
    await v.wait()

    if delete_after:
        await m.delete(delay=0)

    try:
        return v.children[0].values
    except IndexError:
        return None


async def text_channel_input(
    inter: discord.Interaction,
    message: str,
    placeholder: str = "Please select a channel ...",
    delete_after=True,
) -> discord.TextChannel | None:

    v = discord.ui.View(timeout=120)
    v.add_item(ChannelSelectorInput(placeholder=placeholder))

    m = await inter.followup.send(
        embed=discord.Embed(color=int(os.getenv("DEFAULT_COLOR")), description=message), view=v, ephemeral=True
    )
    await v.wait()

    if delete_after:
        await m.delete(delay=0)

    try:
        return v.children[0].values[0]
    except IndexError:
        return None


async def guild_role_input(
    inter: discord.Interaction,
    message: str,
    placeholder: str = "Please select a role ...",
    delete_after=True,
) -> discord.Role | None:

    v = discord.ui.View(timeout=120)
    v.add_item(RoleSelectInput(placeholder=placeholder))

    m = await inter.followup.send(
        embed=discord.Embed(color=int(os.getenv("DEFAULT_COLOR")), description=message), view=v, ephemeral=True
    )
    await v.wait()

    if delete_after:
        await m.delete(delay=0)

    try:
        return v.children[0].values[0]
    except IndexError:
        return None


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
