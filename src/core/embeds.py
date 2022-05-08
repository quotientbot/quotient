from __future__ import annotations
from contextlib import suppress
import typing as T
from core.Context import Context

import discord
from .views import QuotientView
from utils import QuoColor


class EmbedOptions(discord.ui.Select):
    view: EmbedBuilder

    def __init__(self, ctx: Context):
        self.ctx = ctx
        super().__init__(
            placeholder="Select an option to design the message.",
            options=[
                discord.SelectOption(
                    label="Normal Text",
                    description="This is displayed above the embed.",
                    emoji="<:c_:972805722276524092>",
                    value="content",
                ),
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
            modal = MainEdit()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.view.embed.title = modal.m_title.value or ""
            self.view.embed.description = modal.m_description.value or ""
            self.view.embed.set_footer(text=modal.m_footer.value or "", icon_url=self.view.embed.footer.icon_url)

            await self.view.refresh_view()

        elif selected == "thumb":
            modal = InputImage()
            await interaction.response.send_modal(modal)
            await modal.wait()

            if modal._image.value.startswith("http"):
                self.view.embed.set_thumbnail(url=modal._image.value)

            else:
                self.view.embed.set_thumbnail(url=discord.Embed.Empty)

            await self.view.refresh_view()

        elif selected == "image":
            modal = InputImage()
            await interaction.response.send_modal(modal)
            await modal.wait()

            if modal._image.value.startswith("http"):
                self.view.embed.set_image(url=modal._image.value)

            else:
                self.view.embed.set_image(url=discord.Embed.Empty)

            await self.view.refresh_view()

        elif selected == "footer_icon":
            modal = InputImage()
            await interaction.response.send_modal(modal)
            await modal.wait()

            if modal._image.value.startswith("http"):
                self.view.embed.set_footer(icon_url=modal._image.value, text=self.view.embed.footer.text)

            else:
                self.view.embed.set_footer(icon_url=discord.Embed.Empty, text=self.view.embed.footer.text)

            await self.view.refresh_view()

        elif selected == "color":
            modal = Color()
            await interaction.response.send_modal(modal)
            await modal.wait()

            color = 0x36393E

            with suppress(ValueError):
                color = int(str(await QuoColor.convert(self.ctx, modal._color.value)).replace("#", ""), 16)

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
    def fomatted(self):
        return {"content": self.content, "embed": self.embed.to_dict()}

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


class MainEdit(discord.ui.Modal, title="Edit Embed Message"):
    m_title = discord.ui.TextInput(
        label="Title",
        placeholder="Enter text for title of embed here...",
        max_length=256,
        required=False,
        style=discord.TextStyle.short,
    )

    m_description = discord.ui.TextInput(
        label="Description",
        placeholder="Enter text for description of embed here...",
        max_length=4000,
        required=False,
        style=discord.TextStyle.long,
    )

    m_footer = discord.ui.TextInput(
        label="Footer Text",
        placeholder="Enter text for footer of embed here...",
        style=discord.TextStyle.long,
        max_length=2048,
        required=False,
    )


class Content(discord.ui.Modal, title="Edit Message Content"):
    _content = discord.ui.TextInput(
        label="Content",
        placeholder="This text will be displayed over the embed",
        required=False,
        max_length=2000,
        style=discord.TextStyle.long,
    )


class Color(discord.ui.Modal, title="Edit Embed Color"):
    _color = discord.ui.TextInput(
        label="Enter a valid Color",
        placeholder="Examples: red, yellow, #00ffb3, etc.",
        required=False,
        max_length="7",
    )


class InputImage(discord.ui.Modal, title="Edit Image"):
    _image = discord.ui.TextInput(
        label="Input Image URL",
        placeholder="Leave empty to remove Image.",
        required=False,
    )
