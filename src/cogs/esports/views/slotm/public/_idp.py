from __future__ import annotations

import typing as T
from contextlib import suppress

import discord
from models import AssignedSlot, Scrim
from utils import BaseSelector, emote

from ..public import ScrimsSlotmPublicView

__all__ = ("IdpTransfer",)


class IdpTransfer(discord.ui.Button):
    view: ScrimsSlotmPublicView

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction) -> T.Any:
        await interaction.response.defer(thinking=True, ephemeral=True)

        if not await self.view.bot.is_premium_guild(interaction.guild_id):
            return await interaction.followup.send(
                "IDP Transfer feature is only available for premium servers.\n\n"
                f"*This server needs to purchase [Quotient Premium]({self.view.bot.prime_link}) to use this feature.*",
                ephemeral=True,
            )

        if not (slots := await self.view.record.user_slots(interaction.user.id)):
            return await interaction.followup.send("You don't have any slot that can be transferred.", ephemeral=True)

        transfer_view = BaseSelector(interaction.user.id, SlotSelector, bot=self.view.bot, records=slots)
        await interaction.followup.send(
            "Choose a slot to transfer ID-Pass Role to your teammates:", view=transfer_view, ephemeral=True
        )
        await transfer_view.wait()
        if not transfer_view.custom_id:
            return

        scrim_id, slot_id = transfer_view.custom_id.split(":")
        scrim = await Scrim.get(pk=scrim_id)
        _slot = await AssignedSlot.filter(pk=slot_id).first()

        with suppress(ValueError):
            _slot.members.remove(interaction.user.id)

        if not _slot.members:
            return await interaction.followup.send(
                f"{interaction.user.mention}, you cannot transfer ID-Pass role to your teammates "
                "because you didn't mention them during registration.",
                ephemeral=True,
            )

        users = [member async for member in self.view.bot.resolve_member_ids(interaction.guild, _slot.members)]
        if not users:
            return await interaction.followup.send("All your teammates seems to have left the server.", ephemeral=True)

        if len(users) == 1:
            user_id = users[0].id

        else:
            users_view = BaseSelector(interaction.user.id, UserSelector, users=users)
            await interaction.followup.send(
                "Please select your teammate to transfer ID-Pass Role.", view=users_view, ephemeral=True
            )
            await users_view.wait()
            if not users_view.custom_id:
                return

            user_id = int(users_view.custom_id)

        await AssignedSlot.filter(pk=_slot.pk).update(user_id=user_id)
        self.view.bot.loop.create_task(interaction.user.remove_roles(discord.Object(scrim.role_id)))
        self.view.bot.loop.create_task(interaction.guild.get_member(user_id).add_roles(discord.Object(scrim.role_id)))
        return await interaction.followup.send(
            f"{emote.check} | ID-Pass Role & Slot ownership transferred to <@{user_id}>", ephemeral=True
        )


class SlotSelector(discord.ui.Select):
    view: BaseSelector

    def __init__(self, bot, records):
        _options = []
        for record in records[:25]:
            reg_channel = bot.get_channel(record["registration_channel_id"])
            _options.append(
                discord.SelectOption(
                    label=f"Slot {record['num']} ─ #{getattr(reg_channel,'name','deleted-channel')}",
                    description=f"{record['team_name']} (ID: {record['scrim_id']})",
                    value=f"{record['scrim_id']}:{record['assigned_slot_id']}",
                    emoji="📇",
                )
            )

        super().__init__(placeholder="Select slot from this dropdown...", options=_options, max_values=1)

    async def callback(self, interaction: discord.Interaction) -> T.Any:
        await interaction.response.defer()
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class UserSelector(discord.ui.Select):
    view: BaseSelector

    def __init__(self, users: T.List[discord.Member]):
        _options = []
        for user in users:
            _options.append(
                discord.SelectOption(
                    label=f"{user.name}#{user.discriminator}",
                    value=user.id,
                    emoji="📇",
                )
            )

        super().__init__(placeholder="Select your teammate from this dropdown", options=_options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]
