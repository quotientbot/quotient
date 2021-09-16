from discord.invite import I
from ...views.base import EsportsBaseView
from models import Tourney

from core import Context

from utils import string_input

import discord


class EditTourneyEmoji(EsportsBaseView):
    def __init__(self, ctx: Context, *, tourney: Tourney):
        super().__init__(ctx, timeout=30)

        self.ctx = ctx
        self.tourney = tourney

    @staticmethod
    def initial_message(ctx: Context, tourney: Tourney):
        embed = ctx.bot.embed(
            ctx,
            description=(
                f"Emoji Config For {str(tourney)}:\n\n"
                f"• Check Emoji: {tourney.check_emoji}\n"
                f"• Cross Emoji: {tourney.cross_emoji}"
            ),
        )
        return embed

    async def __refresh_embed(self):
        await self.tourney.refresh_from_db()
        try:
            self.message = await self.message.edit(embed=self.initial_message(self.ctx, self.tourney), view=self)
        except:
            await self.on_timeout()

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="tourney_emojis", label="Edit Emojis")
    async def set_emojis(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        e = discord.Embed(color=self.ctx.bot.color, title="Edit tourney emojis")
        e.description = (
            "Which emojis do you want to use for tick and cross in tournament registrations?\n\n"
            "`Please enter two emojis and separate them with a comma`"
        )
        e.set_image(url="https://cdn.discordapp.com/attachments/851846932593770496/888097255607906354/unknown.png")
        e.set_footer(text="The first emoji must be the emoji for tick mark.")

        await interaction.followup.send(embed=e, ephemeral=True)

        emojis = await string_input(self.ctx, self.check, delete_after=True)

        emojis = emojis.strip().split(",")
        if not len(emojis) == 2:
            return await interaction.followup.send("You didn't enter the correct format.", ephemeral=True)

        check, cross = emojis

        for emoji in emojis:
            try:
                await self.message.add_reaction(emoji.strip())
                await self.message.clear_reactions()
            except discord.HTTPException:
                return await interaction.followup.send("One of the emojis you entered is invalid.", ephemeral=True)

        await Tourney.filter(pk=self.tourney.id).update(emojis={"tick": check.strip(), "cross": cross.strip()})
        await self.__refresh_embed()
