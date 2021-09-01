from async_property import async_property
from core import Context
import discord


class SlotReserver(discord.ui.View):
    def __init__(self, ctx: Context):
        super().__init__(timeout=120.0)
        self.ctx = ctx
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

            await self.message.edit(embed=await self.updated_embed, view=self)

    @async_property
    async def updated_embed(self):
        ...

    async def refresh(self):
        ...

    async def ask_embed(self, desc: str, *, image=None):
        embed = discord.Embed(color=self.ctx.bot.color, description=desc, title="Reserved-Slots Editor")
        if image:
            embed.set_image(url=image)
        embed.set_footer(text=f"Reply with 'cancel' to stop this process.")

        return await self.ctx.send(embed=embed)

    async def error_embed(self, desc: str):
        embed = discord.Embed(color=discord.Color.red(), title="Whoopsi-Doopsi", description=desc)
        await self.ctx.send(embed=embed, delete_after=2)

    @discord.ui.button()
    async def reserve_slot(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button()
    async def remove_reserved(self, button: discord.Button, interaction: discord.Interaction):
        ...
