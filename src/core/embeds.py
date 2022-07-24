from __future__ import annotations

import typing as T
from contextlib import suppress

import discord

from core.Context import Context
from utils import QuoColor

from .views import QuotientView, QuoInput


class EmbedOptions(discord.ui.Select):
    view: EmbedBuilder

    def __init__(self, ctx: Context):
        self.ctx = ctx
        super().__init__(
            placeholder="Select an option to design the message.",
            options=[
                # discord.SelectOption(
                #     label="Normal Text",
                #     description="This is displayed above the embed.",
                #     emoji="<:c_:972805722276524092>",
                #     value="content",
                # ),
                discord.SelectOption(
                    label="Edit Message (Title, Description, Footer)",
                    emoji="<:menu:972807297812275220>",
                    value="main",
                    description="Edit your embed title, description, and footer.",
                ),
                discord.SelectOption(
                    label="Edit Thumbnail Image",
                    description="Small Image on the right side of embed",
                    emoji="<:thumbnail:972829519566233640>",
                    value="thumb",
                ),
                discord.SelectOption(
                    label="Edit Main Image",
                    description="Edit your embed Image",
                    emoji="<:image:972786493263323136>",
                    value="image",
                ),
                discord.SelectOption(
                    label="Edit Footer Icon",
                    description="Small icon near footer message",
                    emoji="<:image:972786493263323136>",
                    value="footer_icon",
                ),
                discord.SelectOption(
                    label="Edit Embed Color",
                    description="Change the color of the embed",
                    emoji="<:color:972832294857482271>",
                    value="color",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        if (selected := self.values[0]) == "content":
            modal = Content()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.view.content = modal._content.value or ""

            await self.view.refresh_view()

        elif selected == "main":
            modal = QuoInput("Set Embed Message")
            modal.add_item(
                discord.ui.TextInput(
                    label="Title",
                    placeholder="Enter text for title of embed here...",
                    max_length=256,
                    required=False,
                    style=discord.TextStyle.short,
                    default=self.view.embed.title,
                )
            )
            modal.add_item(
                discord.ui.TextInput(
                    label="Description",
                    placeholder="Enter text for description of embed here...",
                    max_length=4000,
                    required=False,
                    style=discord.TextStyle.long,
                    default=self.view.embed.description,
                )
            )
            modal.add_item(
                discord.ui.TextInput(
                    label="Footer Text",
                    placeholder="Enter text for footer of embed here...",
                    style=discord.TextStyle.long,
                    max_length=2048,
                    required=False,
                    default=self.view.embed.footer.text,
                )
            )
            await interaction.response.send_modal(modal)
            await modal.wait()

            t, d, f = str(modal.children[0]), str(modal.children[1]), str(modal.children[2])

            self.view.embed.title = t or None
            self.view.embed.description = d or None
            self.view.embed.set_footer(text=f or None, icon_url=self.view.embed.footer.icon_url)

            await self.view.refresh_view()

        elif selected == "thumb":
            modal = QuoInput("Edit Thumbnail Image")
            modal.add_item(
                discord.ui.TextInput(
                    label="Enter Image URL (Optional)",
                    placeholder="Leave empty to remove Image.",
                    required=False,
                    default=getattr(self.view.embed.thumbnail, "url", None),
                )
            )
            await interaction.response.send_modal(modal)
            await modal.wait()
            url = str(modal.children[0]) or None

            if not url or not url.startswith("https"):
                self.view.embed.set_thumbnail(url=None)

            else:
                self.view.embed.set_thumbnail(url=url)
            await self.view.refresh_view()

        elif selected == "image":
            modal = QuoInput("Edit Main Image")
            modal.add_item(
                discord.ui.TextInput(
                    label="Enter Image URL (Optional)",
                    placeholder="Leave empty to remove Image.",
                    required=False,
                    default=getattr(self.view.embed.image, "url", None),
                )
            )
            await interaction.response.send_modal(modal)
            await modal.wait()
            url = str(modal.children[0]) or None

            if not url or not url.startswith("https"):
                self.view.embed.set_image(url=None)

            else:
                self.view.embed.set_image(url=url)

            await self.view.refresh_view()

        elif selected == "footer_icon":
            modal = QuoInput("Edit Footer Icon")
            modal.add_item(
                discord.ui.TextInput(
                    label="Enter Image URL (Optional)",
                    placeholder="Leave empty to remove Icon.",
                    required=False,
                    default=getattr(self.view.embed.footer, "icon_url", None),
                )
            )
            await interaction.response.send_modal(modal)
            await modal.wait()
            url = str(modal.children[0]) or None

            if not url or not url.startswith("https"):
                self.view.embed.set_footer(icon_url=None, text=self.view.embed.footer.text)

            else:
                self.view.embed.set_footer(icon_url=url, text=self.view.embed.footer.text)

            await self.view.refresh_view()

        elif selected == "color":
            modal = QuoInput("Set Embed Color")
            modal.add_item(
                discord.ui.TextInput(
                    label="Enter a valid Color",
                    placeholder="Examples: red, yellow, #00ffb3, etc.",
                    required=False,
                    max_length="7",
                )
            )
            await interaction.response.send_modal(modal)
            await modal.wait()

            color = 0x36393E

            with suppress(ValueError):
                if c := str(modal.children[0]):
                    color = int(str(await QuoColor.convert(self.ctx, c)).replace("#", ""), 16)

            self.view.embed.color = color

            await self.view.refresh_view()


class EmbedBuilder(QuotientView):
    def __init__(self, ctx: Context, **kwargs):
        super().__init__(ctx, timeout=100)

        self.ctx = ctx
        self.add_item(EmbedOptions(self.ctx))

        for _ in kwargs.get("items", []):  # to add extra buttons and handle this view externally
            self.add_item(_)

    @property
    def formatted(self):
        return self.embed.to_dict()

    async def refresh_view(self, to_del: discord.Message = None):
        if to_del:
            await self.ctx.safe_delete(to_del)

        with suppress(discord.HTTPException):
            self.message = await self.message.edit(content=self.content, embed=self.embed, view=self)

    async def rendor(self, **kwargs):
        self.message: discord.Message = await self.ctx.send(
            kwargs.get("content", ""),
            embed=kwargs.get("embed", self.help_embed),
            view=self,
        )

        self.content = self.message.content
        self.embed = self.message.embeds[0]

    @property
    def help_embed(self):
        return (
            discord.Embed(color=self.bot.color, title="Title", description="Description")
            .set_thumbnail(
                url="https://cdn.discordapp.com/attachments/853174868551532564/860464565338898472/embed_thumbnail.png"
            )
            .set_image(url="https://cdn.discordapp.com/attachments/853174868551532564/860462053063393280/embed_image.png")
            .set_footer(
                text="Footer Message",
                icon_url="https://media.discordapp.net/attachments/853174868551532564/860464989164535828/embed_footer.png",
            )
        )


class Content(discord.ui.Modal, title="Edit Message Content"):
    _content = discord.ui.TextInput(
        label="Content",
        placeholder="This text will be displayed over the embed",
        required=False,
        max_length=2000,
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
