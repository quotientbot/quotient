from ..views.base import EsportsBaseView

from ast import literal_eval as leval
from utils import string_input, truncate_string, QuoColor
from async_property import async_property

from functools import wraps
from models import Scrim
from core import Context
import discord


class SlotlistFormatter(EsportsBaseView):
    def __init__(self, ctx: Context, *, scrim: Scrim):
        super().__init__(ctx, timeout=60)
        self.ctx = ctx
        self.scrim = scrim

        self.__current_embed: discord.Embed = None

    @staticmethod
    def updated_embed(scrim: Scrim) -> discord.Embed:
        if scrim.slotlist_format:
            edict = leval(scrim.slotlist_format)
            embed = discord.Embed.from_dict(edict)

            if embed.color == discord.Embed.Empty:
                embed.color = 0x2F3136

        else:
            embed = discord.Embed(color=0x00FFB3, title=f"{scrim.name} Slotlist")

        description = embed.description.replace("\n" * 3, "") if embed.description else ""

        slotstr = "Slot No.  -->  Team Name\n"
        embed.description = f"```{slotstr * 6}```{description}"

        return embed

    def __create_current_embed(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            self: SlotlistFormatter = args[0]
            if not self.__current_embed:
                self.__current_embed = self.updated_embed(self.scrim)

            await args[2].response.defer(ephemeral=True)

            return await func(*args, **kwargs)

        return wrapper

    async def _refresh_embed(self):
        await self.message.edit(embed=self.__current_embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="title", label="Title", emoji="🇹")
    @__create_current_embed
    async def set_title(self, button: discord.Button, interaction: discord.Interaction):

        msg = await self.ask_embed(
            "What do you want the title of slotlists to be?\n\n"
            "`Keep the title under 100 characters`\n"
            "Enter `none` to remove the title field."
        )

        title = await string_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(msg)

        if (_title := title.strip().lower()) == "none":
            self.__current_embed.title = discord.Embed.Empty

        else:
            self.__current_embed.title = truncate_string(_title, 100)

        await self._refresh_embed()

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="description", label="Description", emoji="🇩")
    @__create_current_embed
    async def set_description(self, button: discord.Button, interaction: discord.Interaction):

        msg = await self.ask_embed(
            "What do you want the description of slotlists to be?\n\n"
            "`Keep the title under 1000 characters`\n"
            "Enter `none` to remove the decription field."
        )

        description = await string_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(msg)

        if (_desc := description.strip().lower()) == "none":
            slotstr = "Slot No.  -->  Team Name\n"
            self.__current_embed.description = f"```{slotstr * 6}```{description}"

        else:
            self.__current_embed.description += truncate_string("\n" + _desc, 1000)

        await self._refresh_embed()

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="footer", label="Footer", emoji="🇸")
    @__create_current_embed
    async def set_footer(self, button: discord.Button, interaction: discord.Interaction):
        msg = await self.ask_embed(
            "What do you want the footer of slotlists to be?\n\n"
            "`Keep the title under 1000 characters`\n"
            "Enter `none` to remove the footer field."
        )

        footer = await string_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(msg)

        if (_title := footer.strip().lower()) == "none":
            self.__current_embed.set_footer(text=discord.Embed.Empty)

        else:
            self.__current_embed.set_footer(text=truncate_string(_title, 1000))

        await self._refresh_embed()

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="thumbnail", label="Thumbnail", emoji="📸", row=2)
    @__create_current_embed
    async def set_thumbnail(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="image", label="Image", emoji="🖼️", row=2)
    @__create_current_embed
    async def set_image(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="color", label="Color", emoji="🌈", row=2)
    @__create_current_embed
    async def set_color(self, button: discord.Button, interaction: discord.Interaction):
        msg = await self.ask_embed(
            "What do you want the color of slotlists to be?\n\n"
            "Color can be a hex value like `#00ffb3` or normal value like `red` or `green`\n"
            "Enter `none` to keep the color invisible."
        )

        color = await string_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(msg)

        if (_color := color.strip().lower()) == "none":
            self.__current_embed.color = 0x2F3136

        else:
            _color = await QuoColor().convert(self.ctx, _color)
            self.__current_embed.color = _color

        await self._refresh_embed()

    @discord.ui.button(style=discord.ButtonStyle.red, custom_id="abort", label="Abort", row=3)
    @__create_current_embed
    async def abort(self, button: discord.Button, interaction: discord.Interaction):
        await self.on_timeout()

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="check", label="Save", row=3)
    @__create_current_embed
    async def save(self, button: discord.Button, interaction: discord.Interaction):
        ...
