from core import Context
import discord


class EsportsBaseView(discord.ui.View):
    def __init__(self, ctx: Context, **kwargs):
        super().__init__(timeout=60)

        self.ctx = ctx
        self.title = kwargs.get("title", "")

        self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "Sorry, you can't use this interaction as it is not started by you.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if hasattr(self, "message"):
            for b in self.children:

                b.style, b.disabled = discord.ButtonStyle.grey, True

            await self.message.edit(embed=self.message.embeds[0], view=self)

    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        self.ctx.bot.dispatch("command_error", self.ctx, error)

    async def ask_embed(self, desc: str, *, image=None):
        embed = discord.Embed(color=self.ctx.bot.color, description=desc, title=self.title)
        if image:
            embed.set_image(url=image)
        embed.set_footer(text=f"Reply with 'cancel' to stop this process.")

        return await self.ctx.send(embed=embed, embed_perms=True)

    async def error_embed(self, desc: str):
        embed = discord.Embed(color=discord.Color.red(), title="Whoopsi-Doopsi", description=desc)
        await self.ctx.send(embed=embed, delete_after=2, embed_perms=True)
