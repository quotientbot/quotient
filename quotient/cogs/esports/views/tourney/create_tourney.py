import discord
from cogs.esports.views.tourney.utility import buttons
from discord.ext import commands
from lib import DIAMOND, keycap_digit
from models import Tourney

from . import TourneyView


class CreateTourneyView(TourneyView):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, timeout=100)

        self.record: Tourney = Tourney(guild_id=ctx.guild.id)

        self.add_item(buttons.SetRegChannel(ctx, emoji=keycap_digit(1)))
        self.add_item(buttons.SetConfirmChannel(ctx, emoji=keycap_digit(2)))
        self.add_item(buttons.SetSuccessRole(ctx, emoji=keycap_digit(3)))
        self.add_item(buttons.SetMentions(ctx, emoji=keycap_digit(4)))
        self.add_item(buttons.SetGroupSize(ctx, emoji=keycap_digit(5)))
        self.add_item(buttons.SetTotalSlots(ctx, emoji=keycap_digit(6)))
        self.add_item(buttons.SetReactions(ctx, emoji=keycap_digit(7)))
        self.add_item(buttons.DiscardChanges(ctx, label="Cancel"))
        self.add_item(buttons.SaveTourney(ctx))

    def initial_msg(self) -> discord.Embed:
        e = discord.Embed(
            color=self.bot.color, title="Enter details & Press Create Tourney", url=self.bot.config("SUPPORT_SERVER_LINK")
        )

        fields = {
            "Reg. Channel": getattr(self.record.registration_channel, "mention", "`Not-Set`"),
            "Confirm Channel": getattr(self.record.confirm_channel, "mention", "`Not-Set`"),
            "Success Role": getattr(self.record.success_role, "mention", "`Not-Set`"),
            "Req. Mentions": f"`{self.record.required_mentions}`",
            "Teams per Group": f"`{self.record.group_size or 'Not-Set'}`",
            "Total Slots": f"`{self.record.total_slots or 'Not-Set'}`",
            f"Reactions {DIAMOND}": f"{self.record.reactions[0]}, {self.record.reactions[1]}",
        }

        for idx, (name, value) in enumerate(fields.items(), start=1):
            e.add_field(
                name=f"{keycap_digit(idx)} {name}:",
                value=value,
            )

        return e

    async def refresh_view(self):
        e = self.initial_msg()

        if all(
            (
                self.record.registration_channel_id,
                self.record.success_role_id,
                self.record.confirm_channel_id,
                self.record.total_slots,
                self.record.group_size,
            )
        ):
            self.children[-1].disabled = False

        try:
            self.message = await self.message.edit(embed=e, view=self)
        except discord.HTTPException:
            await self.on_timeout()
