from utils.inputs import image_input
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

        self.__slotstr = "Slot No.  -->  Team Name\n"
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
        self.message = await self.message.edit(embed=self.__current_embed, view=self)

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
            self.__current_embed.title = truncate_string(title.strip(), 100)

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
            self.__current_embed.description = f"```{self.__slotstr * 6}```{description}"

        else:
            self.__current_embed.description += truncate_string("\n" + description.strip(), 1000)

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
            self.__current_embed.set_footer(text=truncate_string(footer.strip(), 1000))

        await self._refresh_embed()

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="thumbnail", label="Thumbnail", emoji="📸", row=2)
    @__create_current_embed
    async def set_thumbnail(self, button: discord.Button, interaction: discord.Interaction):
        msg = await self.ask_embed(
            "Which image do you want to use as thumbnail of slotlists?\n\n"
            "`You can send an attachment or a valid Image URL`.\n"
            "Enter `none` to remove previous thumbnail."
        )

        image = await image_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(msg)

        self.__current_embed.set_thumbnail(url=image) if image else self.__current_embed.set_thumbnail(
            url=discord.Embed.Empty
        )

        await self._refresh_embed()

    @discord.ui.button(style=discord.ButtonStyle.grey, custom_id="image", label="Image", emoji="🖼️", row=2)
    @__create_current_embed
    async def set_image(self, button: discord.Button, interaction: discord.Interaction):
        msg = await self.ask_embed(
            "Which image do you want to add in slotlists?\n\n"
            "`You can send an attachment or a valid Image URL`.\n"
            "Enter `none` to remove previous image."
        )

        image = await image_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(msg)

        self.__current_embed.set_image(url=image) if image else self.__current_embed.set_image(url=discord.Embed.Empty)

        await self._refresh_embed()

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

        self.__current_embed.description = self.__current_embed.description.replace(f"```{self.__slotstr * 6}```", "")
        _dict = self.__current_embed.to_dict()

        await Scrim.filter(pk=self.scrim.id).update(slotlist_format=str(_dict))
        await self.ctx.success("Your new slotlist definitely looks sexier.", delete_after=3)

        await self.on_timeout()
