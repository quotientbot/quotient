import discord
from core import Context
from models import Scrim
from ..views import EsportsBaseView


class ScrimsToggle(EsportsBaseView):
    def __init__(self,ctx:Context,*,scrim:Scrim):
        super().__init__(ctx, timeout=60)
        self.ctx = ctx
        self.scrim = scrim


    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="scrim_toggle", label="Registration")
    async def scrims(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="autoclean_toggle", label="Autoclean")
    async def autoclean(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="multiregister_toggle", label="Multiregister")
    async def multiregister(self, button: discord.Button, interaction: discord.Interaction):
        ...

    
