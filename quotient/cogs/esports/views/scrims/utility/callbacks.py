import os
from typing import NamedTuple

import discord
from cogs.premium import RequirePremiumView
from lib import (
    guild_role_input,
    integer_input_modal,
    send_error_embed,
    send_simple_embed,
    text_input,
    time_input_modal,
)
from models import Guild, IdpShareType

from ...scrims import ScrimsBtn
from .selectors import WeekDaysSelector


async def edit_required_mentions(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    req_mentions = await integer_input_modal(
        inter,
        title="Required Mentions",
        label="How many mentions are required to register?",
        placeholder="Enter a number in range 0-5",
        default=cls.view.record.required_mentions,
    )

    if req_mentions is None:
        return await send_error_embed(inter.channel, "You failed to enter a valid number! Please try again.", 5)

    if not 0 <= req_mentions <= 5:
        return await send_error_embed(inter.channel, "Mentions must be in range 0-5.", 5)

    cls.view.record.required_mentions = req_mentions

    await cls.view.refresh_view()


async def edit_total_slots(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    total_slots = await integer_input_modal(
        inter,
        title="Total Slots",
        label="How many total slots are there?",
        placeholder="Enter a number in range 1-30",
        default=cls.view.record.total_slots,
    )

    if total_slots is None:
        return await send_error_embed(inter.channel, "You failed to enter a valid number! Please try again.", 5)

    if not 1 <= total_slots <= 30:
        return await send_error_embed(inter.channel, "Total Slots must be in range 1-30.", 5)

    cls.view.record.total_slots = total_slots

    await cls.view.refresh_view()


async def edit_reg_start_time(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    reg_start_time = await time_input_modal(
        inter,
        title="Registration Start Time (IST - UTC+5:30)",
        label="Enter registration start time.",
        default=cls.view.record.reg_start_time.strftime("%I:%M%p") if cls.view.record.reg_start_time else None,
    )

    if reg_start_time is None:
        return await send_error_embed(
            inter.channel,
            "You failed to enter registration start time in valid format! Take a look at the examples below:",
            delete_after=5,
            image_url="https://cdn.discordapp.com/attachments/851846932593770496/958291942062587934/timex.gif",
        )

    cls.view.record.reg_start_time = reg_start_time
    await cls.view.refresh_view()


async def edit_match_start_time(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    match_start_time = await time_input_modal(
        inter,
        title="Match Start Time (IST - UTC+5:30)",
        label="Time the actual game starts (BGMI, FF, etc)",
        default=cls.view.record.match_start_time.strftime("%I:%M%p") if cls.view.record.match_start_time else None,
    )

    if match_start_time is None:
        return await send_error_embed(
            inter.channel,
            "You failed to enter match start time in valid format! Take a look at the examples below:",
            delete_after=5,
            image_url="https://cdn.discordapp.com/attachments/851846932593770496/958291942062587934/timex.gif",
        )

    cls.view.record.match_start_time = match_start_time
    await cls.view.refresh_view()


async def edit_reg_start_ping_role(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    await inter.response.defer()

    if cls.view.record.reg_start_ping_role_id:
        cls.view.record.reg_start_ping_role_id = None
        return await cls.view.refresh_view()

    m = await send_simple_embed(inter.channel, "Please mention the role to ping when registration starts.")

    role = await guild_role_input(
        cls.ctx,
        timeout=120,
        delete_after=True,
    )
    await m.delete(delay=0)

    if not role:
        return

    cls.view.record.reg_start_ping_role_id = role.id
    await cls.view.refresh_view()


async def edit_reg_open_role(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    await inter.response.defer()

    if cls.view.record.open_role_id:
        cls.view.record.open_role_id = None
        return await cls.view.refresh_view()

    m = await send_simple_embed(
        inter.channel,
        "Please mention the role for which registration channel is opened. (Given send messages permissions when registration starts)",
    )

    role = await guild_role_input(
        cls.ctx,
        timeout=120,
        delete_after=True,
    )
    await m.delete(delay=0)

    if not role:
        return

    cls.view.record.open_role_id = role.id
    await cls.view.refresh_view()


async def edit_allow_multiple_registrations(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    await inter.response.defer()

    cls.view.record.allow_multiple_registrations = not cls.view.record.allow_multiple_registrations
    await cls.view.refresh_view()


async def edit_allow_without_teamname(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    await inter.response.defer()

    cls.view.record.allow_without_teamname = not cls.view.record.allow_without_teamname
    await cls.view.refresh_view()


async def edit_registration_open_days(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    v = discord.ui.View(timeout=100)
    v.add_item(WeekDaysSelector())

    await inter.response.send_message("Select weekdays on which registration should be opened:", view=v, ephemeral=True)
    await v.wait()

    if v.selected_days:
        cls.view.record.registration_open_days = [int(d) for d in v.selected_days]
        await cls.view.refresh_view()


async def edit_required_lines(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    if cls.view.record.required_lines:
        cls.view.record.required_lines = 0
        return await cls.view.refresh_view()

    required_lines = await integer_input_modal(
        inter,
        title="Useful to ignore incomplete info in Reg Msg",
        label="Atleast how many lines are req in reg msg?",
        placeholder="Enter a number in range 0-10",
        default=cls.view.record.required_lines,
    )

    if required_lines is None:
        return await send_error_embed(inter.channel, "You failed to enter a valid number! Please try again.", 5)

    if not 0 <= required_lines <= 10:
        return await send_error_embed(inter.channel, "Min Required Lines must be in range 0-10.", 5)

    cls.view.record.required_lines = required_lines
    await cls.view.refresh_view()


async def edit_allow_duplicate_mentions(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    await inter.response.defer()

    cls.view.record.allow_duplicate_mentions = not cls.view.record.allow_duplicate_mentions
    await cls.view.refresh_view()


async def edit_allow_duplicate_teamname(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    await inter.response.defer()

    cls.view.record.allow_duplicate_teamname = not cls.view.record.allow_duplicate_teamname
    await cls.view.refresh_view()


async def edit_auto_delete_extra_messages(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    await inter.response.defer()

    cls.view.record.autodelete_extra_msges = not cls.view.record.autodelete_extra_msges
    await cls.view.refresh_view()


async def edit_auto_delete_rejected_registrations(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    await inter.response.defer()

    cls.view.record.autodelete_rejected_registrations = not cls.view.record.autodelete_rejected_registrations
    await cls.view.refresh_view()


async def edit_registration_end_ping_role(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    await inter.response.defer()

    if cls.view.record.reg_end_ping_role_id:
        cls.view.record.reg_end_ping_role_id = None
        return await cls.view.refresh_view()

    m = await send_simple_embed(inter.channel, "Please mention the role to ping when registration ends.")

    role = await guild_role_input(
        cls.ctx,
        timeout=120,
        delete_after=True,
    )
    await m.delete(delay=0)

    if not role:
        return

    cls.view.record.reg_end_ping_role_id = role.id
    await cls.view.refresh_view()


async def edit_channel_autoclean_time(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    if cls.view.record.autoclean_channel_time:
        await inter.response.defer()
        cls.view.record.autoclean_channel_time = None
        return await cls.view.refresh_view()

    channel_autoclean_time = await time_input_modal(
        inter,
        title="Channel Autoclean Time (IST - UTC+5:30)",
        label="Time when reg channel should be cleaned?",
        default=cls.view.record.autoclean_channel_time.strftime("%I:%M%p") if cls.view.record.autoclean_channel_time else None,
    )

    if channel_autoclean_time is None:
        return await send_error_embed(
            inter.channel,
            "You failed to enter channel autoclean time in valid format! Take a look at the examples below:",
            delete_after=5,
            image_url="https://cdn.discordapp.com/attachments/851846932593770496/958291942062587934/timex.gif",
        )

    cls.view.record.autoclean_channel_time = channel_autoclean_time
    await cls.view.refresh_view()


async def edit_registration_auto_end_time(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    reg_auto_end_time = await time_input_modal(
        inter,
        title="Registration Auto-End Time (IST - UTC+5:30)",
        label="Time reg should be auto-ended if not already?",
        default=cls.view.record.reg_auto_end_time.strftime("%I:%M%p") if cls.view.record.reg_auto_end_time else None,
    )

    if reg_auto_end_time is None:
        return await send_error_embed(
            inter.channel,
            "You failed to enter registration auto-end time in valid format! Take a look at the examples below:",
            delete_after=5,
            image_url="https://cdn.discordapp.com/attachments/851846932593770496/958291942062587934/timex.gif",
        )

    cls.view.record.reg_auto_end_time = reg_auto_end_time
    await cls.view.refresh_view()


async def edit_share_idp_with(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    await inter.response.defer()

    if cls.view.record.idp_share_type == IdpShareType.LEADER_ONLY:
        cls.view.record.idp_share_type = IdpShareType.ALL_TEAM_MEMBERS

    else:
        cls.view.record.idp_share_type = IdpShareType.LEADER_ONLY

    await cls.view.refresh_view()


async def edit_slotlist_start_from(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    slotlist_start_from = await integer_input_modal(
        inter,
        title="Slotlist Should Start From?",
        label="Enter the first slot number of slotlist.",
        placeholder=f"Enter a num in range 1-{cls.view.record.total_slots}",
        default=cls.view.record.slotlist_start_from,
    )

    if slotlist_start_from is None:
        return await send_error_embed(inter.channel, "You failed to enter a valid number! Please try again.", 5)

    if not 1 <= slotlist_start_from <= 30:
        return await send_error_embed(
            inter.channel, f"'Slotlist Start From' must be in range 1-{cls.view.record.slotlist_start_from}.", 5
        )

    cls.view.record.slotlist_start_from = slotlist_start_from
    await cls.view.refresh_view()


async def edit_auto_send_slotlist(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    await inter.response.defer()

    cls.view.record.autosend_slotlist = not cls.view.record.autosend_slotlist
    await cls.view.refresh_view()


async def edit_reactions(cls: discord.ui.Select | ScrimsBtn, inter: discord.Interaction):
    await inter.response.defer()

    guild = await Guild.get(pk=inter.guild_id)

    if not guild.is_premium:
        v = RequirePremiumView(f"Upgrade to Quotient Pro to use custom reactions.")

        return await inter.followup.send(embed=v.premium_embed, view=v, ephemeral=True)

    e = discord.Embed(color=int(os.getenv("DEFAULT_COLOR")), title="Edit scrims emojis")

    e.description = (
        "Which emojis do you want to use for tick and cross in scrims registrations? Note that both emojis must be in this server.\n\n"
        "`Please enter two emojis and separate them with a comma`"
    )

    e.set_image(url="https://cdn.discordapp.com/attachments/851846932593770496/888097255607906354/unknown.png")
    e.set_footer(text="The first emoji must be the emoji for tick mark.")

    m = await inter.followup.send(embed=e)
    emojis = await text_input(cls.ctx, delete_after=True)

    await m.delete(delay=0)

    emojis = emojis.strip().split(",")
    if not len(emojis) == 2:
        return await send_error_embed(inter.channel, "You didn't enter emojis in correct format.", 5)

    check, cross = emojis

    for idx, emoji in enumerate(emojis, start=1):
        try:
            await cls.view.message.add_reaction(emoji.strip())
            await cls.view.message.clear_reactions()
        except discord.HTTPException:
            return await inter.followup.send(
                embed=cls.view.bot.error_embed(f"Emoji {idx} is not valid, Please make sure it is present in this server."),
                ephemeral=True,
            )

    cls.view.record.reactions = [check.strip(), cross.strip()]
    await cls.view.refresh_view()


class EditOption(NamedTuple):
    label: str
    description: str
    premium_guild_only: bool
    handler: callable


EDIT_OPTIONS = [
    EditOption(
        label="Required Mentions",
        description="Set the number of mentions required to register",
        premium_guild_only=False,
        handler=edit_required_mentions,
    ),
    EditOption(
        label="Total Slots",
        description="Set the total slots for the scrim",
        premium_guild_only=False,
        handler=edit_total_slots,
    ),
    EditOption(
        label="Registration Start Time",
        description="Set the registration start time",
        premium_guild_only=False,
        handler=edit_reg_start_time,
    ),
    EditOption(
        label="Match Start Time",
        description="Set the match start time (Actual Game of BGMI, FF, etc)",
        premium_guild_only=False,
        handler=edit_match_start_time,
    ),
    EditOption(
        label="Registration Start Ping Role",
        description="Set the role to ping when registration starts",
        premium_guild_only=False,
        handler=edit_reg_start_ping_role,
    ),
    EditOption(
        label="Registration Open Role",
        description="Set the role to ping when registration opens",
        premium_guild_only=False,
        handler=edit_reg_open_role,
    ),
    EditOption(
        label="Allow Multiple Registrations",
        description="Allow users to register multiple times",
        premium_guild_only=False,
        handler=edit_allow_multiple_registrations,
    ),
    EditOption(
        label="Allow Without Teamname",
        description="Allow users to register without a teamname",
        premium_guild_only=False,
        handler=edit_allow_without_teamname,
    ),
    EditOption(
        label="Registration Open Days",
        description="Set the days when registration is open",
        premium_guild_only=False,
        handler=edit_registration_open_days,
    ),
    EditOption(
        label="Required Lines",
        description="Set the number of lines required in registration",
        premium_guild_only=True,
        handler=edit_required_lines,
    ),
    EditOption(
        label="Allow Duplicate Mentions",
        description="Allow duplicate mentions in registration",
        premium_guild_only=True,
        handler=edit_allow_duplicate_mentions,
    ),
    EditOption(
        label="Allow Duplicate Teamname",
        description="Allow duplicate teamnames in registration",
        premium_guild_only=True,
        handler=edit_allow_duplicate_teamname,
    ),
    EditOption(
        label="Auto-Delete Extra Messages",
        description="Auto-delete extra messages in registration",
        premium_guild_only=True,
        handler=edit_auto_delete_extra_messages,
    ),
    EditOption(
        label="Auto-Delete Rejected Registrations",
        description="Auto-delete rejected registrations",
        premium_guild_only=True,
        handler=edit_auto_delete_rejected_registrations,
    ),
    EditOption(
        label="Registration End Ping Role",
        description="Set the role to ping when registration ends",
        premium_guild_only=True,
        handler=edit_registration_end_ping_role,
    ),
    EditOption(
        label="Channel Autoclean Time",
        description="Set the time to autoclean the channel",
        premium_guild_only=True,
        handler=edit_channel_autoclean_time,
    ),
    EditOption(
        label="Registration Auto-End Time",
        description="Set the time to auto-end registration",
        premium_guild_only=True,
        handler=edit_registration_auto_end_time,
    ),
    EditOption(
        label="Share IDP With",
        description="Set the type of IDP sharing",
        premium_guild_only=True,
        handler=edit_share_idp_with,
    ),
    EditOption(
        label="Slotlist Start From",
        description="Set the first slot number of slotlist",
        premium_guild_only=True,
        handler=edit_slotlist_start_from,
    ),
    EditOption(
        label="Auto-Send Slotlist",
        description="Auto send the slotlist after reg ends.",
        premium_guild_only=True,
        handler=edit_auto_send_slotlist,
    ),
    EditOption(
        label="Reactions",
        description="Set the tick / cross reactions for the scrim",
        premium_guild_only=True,
        handler=edit_reactions,
    ),
]
