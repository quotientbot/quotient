from contextlib import suppress
import aiohttp
import asyncio
import dateparser
from datetime import datetime, timedelta
from discord.ext.commands.converter import RoleConverter, TextChannelConverter, MemberConverter

from utils.default import keycap_digit
from .exceptions import InputError
from constants import IST
import discord


async def safe_delete(message) -> bool:
    try:
        await message.delete()
    except (discord.Forbidden, discord.NotFound):
        return False
    else:
        return True


async def channel_input(ctx, check, timeout=120, delete_after=False):
    try:
        message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
        channel = await TextChannelConverter().convert(ctx, message.content)
    except asyncio.TimeoutError:
        raise InputError("You failed to select a channel in time. Try again!")

    else:
        if not channel.permissions_for(ctx.me).read_messages:
            raise InputError(f"Unfortunately, I don't have send messages permissions in {channel.mention}.")

        if delete_after:
            await safe_delete(message)

        return channel


async def role_input(ctx, check, timeout=120, hierarchy=True, delete_after=False):
    try:
        message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
        role = await RoleConverter().convert(ctx, message.content)
    except asyncio.TimeoutError:
        raise InputError("You failed to select a role in time. Try again!")

    else:
        if role.managed:
            raise InputError(f"Role is an integrated role and cannot be added manually.")
        if hierarchy is True:
            if role > ctx.me.top_role:
                raise InputError(
                    f"The position of {role.mention} is above my top role. So I can't give it to anyone.\nKindly move {ctx.me.top_role.mention} above {role.mention} in Server Settings."
                )

            if ctx.author.id != ctx.guild.owner_id:
                if role > ctx.author.top_role:
                    raise InputError(
                        f"The position of {role.mention} is above your top role {ctx.author.top_role.mention}."
                    )

        if delete_after:
            await safe_delete(message)

        return role


async def member_input(ctx, check, timeout=120, delete_after=False):
    try:
        message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
        member = await MemberConverter().convert(ctx, message.content)

    except asyncio.TimeoutError:
        raise InputError("You failed to mention a member in time. Try again!")

    else:
        if delete_after:
            await safe_delete(message)

        return member


async def integer_input(ctx, check, timeout=120, limits=(None, None), delete_after=False):
    def new_check(message):
        if not check(message):
            return False

        try:
            if limits[1] is not None:
                if len(message.content) > len(str(limits[1])):  # This is for safe side, memory errors u know :)
                    return False

            digit = int(message.content)

        except ValueError:
            return False
        else:
            if not any(limits):  # No Limits
                return True

            low, high = limits

            if all(limits):
                return low <= digit <= high
            if low is not None:
                return low <= digit
            return high <= digit

    try:
        message = await ctx.bot.wait_for("message", check=new_check, timeout=timeout)
    except asyncio.TimeoutError:
        raise InputError("You failed to select a number in time. Try again!")
    else:
        if delete_after:
            await safe_delete(message)

        return int(message.content)


async def time_input(ctx, check, timeout=120, delete_after=False):
    try:
        message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        raise InputError("Timeout, You have't responsed in time. Try again!")
    else:
        try:
            parsed = dateparser.parse(
                message.content,
                settings={
                    "RELATIVE_BASE": datetime.now(tz=IST),
                    "TIMEZONE": "Asia/Kolkata",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                },
            )

            if delete_after:
                await safe_delete(message)

            if datetime.now(tz=IST) > parsed:
                parsed = parsed + timedelta(hours=24)

            return parsed

        except TypeError:
            raise InputError("This isn't valid time format.")


async def string_input(ctx, check, timeout=120, delete_after=False):
    try:
        message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        raise InputError("Took too long. Good Bye.")  # This would sound cooler.
    else:
        if delete_after:
            await safe_delete(message)

        return message.content


async def image_input(ctx, check, timeout=120,delete_after=False):
    try:
        message:discord.Message = await ctx.bot.wait_for("message",check=check, timeout=timeout)
    except asyncio.TimeoutError:
        raise InputError("Took too long. Good Bye.") 
    
    else:
        if delete_after:
            await safe_delete(message)
        
        if message.content.strip().lower() == "none":
            return None
        
        _image_formats = ("image/png", "image/jpeg", "image/jpg", "image/gif")

        if message.attachments and message.attachments[0].content_type in _image_formats:
            return message.attachments[0].proxy_url

        result = None        
        with suppress(aiohttp.InvalidURL):
            res = await ctx.bot.session.get(message.content)
            if res.headers["content-type"] in _image_formats:
                result = message.content
        
        return result 


        

async def text_or_embed(ctx, check, timeout=120, delete_after=False):
    reactions = (keycap_digit(1), keycap_digit(2))

    def react_check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in reactions

    msg = await ctx.simple(
        f"What do you want the content to be?\n\n{keycap_digit(1)} | Simple Text\n{keycap_digit(2)} | Embed"
    )

    for reaction in reactions:
        await msg.add_reaction(reaction)

    reaction, user = await ctx.bot.wait_for("reaction_add", timeout=15, check=react_check)

    if delete_after:
        await safe_delete(msg)

    if str(reaction.emoji) == keycap_digit(1):
        msg = await ctx.simple("Kindly enter the text now.")
        text = await string_input(ctx, check, delete_after=True)

        if delete_after:
            await safe_delete(msg)

        return text

    if str(reaction.emoji) == keycap_digit(2):
        msg = await ctx.simple(f"embed ki .......")
