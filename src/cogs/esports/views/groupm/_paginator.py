from __future__ import annotations

import typing as T

from models.esports.tourney import Tourney, TMSlot, TGroupList

from ..base import EsportsBaseView
from core import Context
import discord

from utils import inputs, emote
from ._refresh import GroupRefresh


class GroupPages(EsportsBaseView):
    def __init__(self, ctx: Context, tourney: Tourney, *, ping_all: bool = True, category=None):
        super().__init__(ctx)

        self.ping_all = ping_all
        self.tourney = tourney

        self.records: T.List[T.List["TMSlot"]] = None
        self.record: T.List[TMSlot] = None

        self.category: discord.CategoryChannel = category
        self.send_to = None

    async def rendor(self, msg: discord.Message):
        self.records = await self.tourney._get_groups()
        self.record = self.records[0]

        self.message = await msg.edit(embed=self.initial_embed, view=self)

    async def refresh_view(self):
        _e = self.initial_embed
        try:
            self.message = await self.message.edit(embed=_e, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    @property
    def send_channel(self):
        index = self.records.index(self.record) + 1
        if self.category:
            return next(c for c in self.category.text_channels if str(index) in c.name)

    @property
    def initial_embed(self):
        current_page = self.records.index(self.record) + 1
        _e = discord.Embed(color=0x00FFB3, title=f"{self.tourney.name} - Group {current_page}")
        _e.set_thumbnail(url=getattr(self.ctx.guild.icon, "url", discord.Embed.Empty))

        _e.description = (
            "```\n"
            + "".join(
                [
                    f"Slot {idx:02}  ->  {slot.team_name}\n"
                    for idx, slot in enumerate(self.record, self.tourney.slotlist_start)
                ]
            )
            + "```"
        )

        if s_t := self.send_to:
            _e.add_field(name="Send to", value=getattr(s_t, "mention", "`Not-Set`"))

        else:
            _e.add_field(name="Send to", value=getattr(self.send_channel, "mention", "`Not-Set`"))

        _e.add_field(name="Ping @everyone", value=("`No`", "`Yes`")[self.ping_all])
        _e.set_footer(text="Page {}/{}".format(current_page, len(self.records)))
        return _e

    @discord.ui.button(emoji="<:left:878668491660623872>")
    async def prev_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        index = self.records.index(self.record)
        if index == 0:
            self.record = self.records[-1]
        else:
            self.record = self.records[index - 1]

        await self.refresh_view()

    @discord.ui.button(label="Skip to...")
    async def skip_to(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        m = await self.ctx.simple("What page do you want to go to? (Enter page number)")
        p = await inputs.integer_input(self.ctx, delete_after=True, timeout=30)
        await self.ctx.safe_delete(m)

        if p > len(self.records) + 1 or p <= 0:
            return await self.ctx.error("Invalid page number.", 4)

        if self.record == self.records[p - 1]:
            return await self.ctx.error("We are already on that page, ya dumb dumb.", 4)

        self.record = self.records[p - 1]
        await self.refresh_view()

    @discord.ui.button(emoji="<:right:878668370331983913>")
    async def next_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        index = self.records.index(self.record)
        if index == len(self.records) - 1:
            self.record = self.records[0]
        else:
            self.record = self.records[index + 1]

        await self.refresh_view()

    @discord.ui.button(label="Give Roles")
    async def give_roles(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        m = await self.ctx.simple(
            f"Mention the role you want to give to Group {self.records.index(self.record) + 1} members."
        )
        role = await inputs.role_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)

        m = await self.ctx.simple(f"Ok, Please wait... {emote.loading}")

        for slot in self.record:
            member = await self.bot.get_or_fetch_member(self.ctx.guild, slot.leader_id)
            if member and not role in member.roles:
                try:
                    await member.add_roles(role)
                except Exception as e:
                    await self.ctx.error(e)

        try:
            await m.edit(
                embed=discord.Embed(
                    color=self.ctx.bot.color,
                    description=f"Done! Given {role.mention} to group {self.records.index(self.record) + 1}.",
                ),
                delete_after=6,
            )
        except discord.HTTPException:
            await self.ctx.simple(
                f"Done, Given {role.mention} to group {self.records.index(self.record) + 1}.", delete_after=6
            )

    @discord.ui.button(label="Send to", row=2, style=discord.ButtonStyle.blurple)
    async def send_channl(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        m = await self.ctx.simple("Mention the channel where you want to send this grouplist.")
        channel = await inputs.channel_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)

        self.send_to = channel
        self.category = channel.category

        await self.refresh_view()

    @discord.ui.button(label="Send", style=discord.ButtonStyle.green, row=2)
    async def send_now(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        c = self.send_to if self.send_to else self.send_channel
        if not c:
            return await self.ctx.error("You need to set a channel first.", 3)

        embed = self.initial_embed

        embed.set_thumbnail(url=discord.Embed.Empty)
        embed.clear_fields()
        embed.set_footer(text=self.ctx.guild.name, icon_url=getattr(self.ctx.guild.icon, "url", discord.Embed.Empty))
        try:
            m = await c.send(
                "@everyone" if self.ping_all else "",
                embed=embed,
                view=GroupRefresh(),
                allowed_mentions=discord.AllowedMentions(everyone=True),
            )

            # I am 100% sure there is a better way to do this but as long as this works, i am good.

            await TGroupList.filter(tourney_id=self.tourney.id, group_number=self.records.index(self.record) + 1).delete()

            await TGroupList.create(
                message_id=m.id,
                channel_id=c.id,
                tourney_id=self.tourney.id,
                group_number=self.records.index(self.record) + 1,
            )
        except Exception as e:
            await self.ctx.error(e)

        await self.ctx.success("GroupList published.", 3)
        await self.refresh_view()
        self.send_to = None
