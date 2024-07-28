import os
from typing import NamedTuple

import discord
from cogs.premium import RequirePremiumView
from lib import (
    guild_role_input,
    integer_input_modal,
    send_error_embed,
    text_channel_input,
    text_input,
    text_input_modal,
)

from quotient.models import Guild

from .. import TourneyBtn


async def edit_required_mentions(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
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


async def edit_group_size(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
    group_size = await integer_input_modal(
        inter,
        title="Group Size",
        label="How many teams should be in each group?",
        placeholder="Enter a number between 2 & 25",
        default=cls.view.record.group_size,
    )

    if group_size is None:
        return await send_error_embed(inter.channel, "You failed to enter a valid number! Please try again.", 5)

    if not 2 <= group_size <= 25:
        return await send_error_embed(inter.channel, "Group size must be in range 2-25.", 5)

    cls.view.record.group_size = group_size

    await cls.view.refresh_view()


async def edit_total_slots(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
    total_slots = await integer_input_modal(
        inter,
        title="Total Slots",
        label="How many total slots are there?",
        placeholder="Enter a number between 1 & 20,000",
        default=cls.view.record.total_slots,
    )

    if total_slots is None:
        return await send_error_embed(inter.channel, "You failed to enter a valid number! Please try again.", 5)

    if not 1 <= total_slots <= 20000:
        return await send_error_embed(
            inter.channel,
            "Total Slots in tourneys must be in range 1-20,000.",
            5,
        )

    cls.view.record.total_slots = total_slots

    await cls.view.refresh_view()


async def edit_reactions(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
    await inter.response.defer()

    guild = await Guild.get(pk=inter.guild_id)

    if not guild.is_premium:
        v = RequirePremiumView(f"Upgrade to Quotient Pro to use custom reactions.")

        return await inter.followup.send(embed=v.premium_embed, view=v, ephemeral=True)

    e = discord.Embed(color=int(os.getenv("DEFAULT_COLOR")), title="Edit tourney emojis")

    e.description = (
        "Which emojis do you want to use for tick and cross in tourney registrations? Note that both emojis must be in this server.\n\n"
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
        except discord.HTTPException:
            return await inter.followup.send(
                embed=cls.view.bot.error_embed(f"Emoji {idx} is not valid, Please make sure it is present in this server."),
                ephemeral=True,
            )

    await cls.view.message.clear_reactions()
    cls.view.record.reactions = [check.strip(), cross.strip()]
    await cls.view.refresh_view()


async def edit_success_role(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
    await inter.response.defer()

    role = await guild_role_input(inter, "Please select the role to be given to successful participants.")

    if not role:
        return await send_error_embed(inter.channel, "You failed to select a valid role! Please try again.", 5)

    if role.managed or role.is_bot_managed() or role.is_integration():
        return await send_error_embed(inter.channel, "You cannot set a bot or managed role as the success role.", 5)

    if role.position >= inter.guild.me.top_role.position:
        return await send_error_embed(
            inter.channel, f"Success Role ({role.mention}) is higher than my top role {inter.guild.me.top_role.mention}.", 5
        )

    if any(
        (
            role.permissions.administrator,
            role.permissions.manage_guild,
            role.permissions.manage_roles,
            role.permissions.manage_channels,
            role.permissions.manage_messages,
            role.permissions.manage_webhooks,
            role.permissions.manage_emojis,
            role.permissions.kick_members,
            role.permissions.ban_members,
        )
    ):
        return await send_error_embed(inter.channel, "You cannot set a role with `moderator permissions` as the success role.", 5)

    cls.view.record.role_id = role.id
    await cls.view.refresh_view()


async def edit_tourney_name(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):

    name = await text_input_modal(inter, "Tourney Name", "Enter the new name for the tourney.", default=cls.view.record.name)

    if not name:
        return await send_error_embed(inter.channel, "You failed to enter a valid name! Please try again.", 5)

    cls.view.record.name = name
    await cls.view.refresh_view()


async def edit_confirm_channel(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
    await inter.response.defer()

    channel = await text_channel_input(inter, "Please select the channel where you want to send slot confirmation messages.")

    if not channel:
        return await send_error_embed(inter.channel, "You failed to select a valid channel! Please try again.", 5)

    cls.view.record.confirm_channel_id = channel.id
    await cls.view.refresh_view()


async def edit_start_ping_role(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
    await inter.response.defer()

    role = await guild_role_input(inter, "Please select the role to be pinged when registration starts.")

    if not role:
        return await send_error_embed(inter.channel, "You failed to select a valid role! Please try again.", 5)

    cls.view.record.start_ping_role_id = role.id
    await cls.view.refresh_view()


async def edit_duplicate_tags(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
    await inter.response.defer()

    cls.view.record.allow_duplicate_mentions = not cls.view.record.allow_duplicate_mentions
    await cls.view.refresh_view()


async def edit_require_team_name(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
    await inter.response.defer()

    cls.view.record.allow_without_teamname = not cls.view.record.allow_without_teamname
    await cls.view.refresh_view()


async def edit_duplicate_team_name(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
    await inter.response.defer()

    cls.view.record.allow_duplicate_teamname = not cls.view.record.allow_duplicate_teamname
    await cls.view.refresh_view()


async def edit_autodel_rejected_reg(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
    await inter.response.defer()

    cls.view.record.autodelete_rejected_registrations = not cls.view.record.autodelete_rejected_registrations
    await cls.view.refresh_view()


async def edit_allow_multi_reg(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
    await inter.response.defer()

    cls.view.record.allow_multiple_registrations = not cls.view.record.allow_multiple_registrations
    await cls.view.refresh_view()


async def edit_required_lines(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
    if cls.view.record.required_lines:
        await inter.response.defer()

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


async def edit_success_message(cls: discord.ui.Select | TourneyBtn, inter: discord.Interaction):
    message = await text_input_modal(
        inter,
        "Success Message",
        "Msg to be sent to successful participants.",
        default=cls.view.record.registration_success_dm_msg,
        max_length=2000,
        min_length=0,
        input_type="long",
    )

    if not message:
        return await send_error_embed(inter.channel, "You failed to enter a valid message! Please try again.", 5)

    cls.view.record.registration_success_dm_msg = message
    await cls.view.refresh_view()


class EditOption(NamedTuple):
    label: str
    description: str
    premium_guild_only: bool
    handler: callable


EDIT_OPTIONS = [
    EditOption("Name", "Change the name of the tourney", False, edit_tourney_name),
    EditOption("Confirmation Channel", "Change the tourney confirmation channel", False, edit_confirm_channel),
    EditOption("Success Role", "Change the role given to successful participants", False, edit_success_role),
    EditOption("Required Mentions", "Change the no of mentions required to register", False, edit_required_mentions),
    EditOption("Total Slots", "Change the total slots available in tourney", False, edit_total_slots),
    EditOption("Reg Start Ping Role", "Change the role to ping when registration starts", False, edit_start_ping_role),
    EditOption("Allow multiple registrations", "Allow users to register multiple times", False, edit_allow_multi_reg),
    EditOption("Require Team Name", "Require users to enter team name during registration", False, edit_require_team_name),
    EditOption("Teams per Group", "Change the number of teams in each group", False, edit_group_size),
    EditOption("Success Message", "Change the message sent to successful participants", True, edit_success_message),
    EditOption("Auto Del Rejected Reg", "Automatically delete rejected registrations", True, edit_autodel_rejected_reg),
    EditOption("Allow duplicate team names", "Allow users to register with same team name", True, edit_duplicate_team_name),
    EditOption("Reactions", "Change the reactions used for registration", True, edit_reactions),
    EditOption("Required Lines", "Change the number of lines required in msg to register", True, edit_required_lines),
    EditOption("Allow Duplicate / Fake Tags", "Allow users to register with duplicate or fake tags", True, edit_duplicate_tags),
]
