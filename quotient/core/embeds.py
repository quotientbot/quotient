import discord
from discord.ext import commands
from lib import CREDIT_CARD, F_WORD, IMAGE_SYMBOL, ColorConverter

from .views import QuoView


class EmbedBuilder(QuoView):
    embed: discord.Embed

    def __init__(
        self,
        ctx: commands.Context,
        embed: discord.Embed = None,
        extra_items: list[discord.ui.Select | discord.ui.Button] = [],
    ):
        super().__init__(ctx, timeout=200)

        self.embed = embed or self.default_embed
        self.add_item(EmbedBuilderOptions(ctx))

        for item in extra_items:
            self.add_item(item)

    @property
    def default_embed(self) -> discord.Embed:
        return (
            discord.Embed(color=self.bot.color, title="Title", description="Description")
            .set_thumbnail(url="https://cdn.discordapp.com/attachments/853174868551532564/860464565338898472/embed_thumbnail.png")
            .set_image(url="https://cdn.discordapp.com/attachments/853174868551532564/860462053063393280/embed_image.png")
            .set_footer(
                text="Footer Message",
                icon_url="https://media.discordapp.net/attachments/853174868551532564/860464989164535828/embed_footer.png",
            )
        )

    async def refresh_view(self):
        try:
            self.message = await self.message.edit(embed=self.embed, view=self)
        except discord.HTTPException:
            pass


class EmbedBuilderModal(discord.ui.Modal):
    def __init__(self, title: str):
        super().__init__(title=title)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()


class EmbedBuilderOptions(discord.ui.Select):
    view: EmbedBuilder

    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        super().__init__(
            placeholder="Select an option to design the message.",
            options=[
                discord.SelectOption(
                    label="Edit Message (Title, Description, Color)",
                    emoji=CREDIT_CARD,
                    value="main",
                    description="Edit your embed title, description, and footer.",
                ),
                discord.SelectOption(
                    label="Edit Images",
                    description="Edit thumbnail or main image of embed.",
                    emoji=IMAGE_SYMBOL,
                    value="image",
                ),
                discord.SelectOption(
                    label="Edit Footer",
                    description="Edit footer text and icon.",
                    emoji=F_WORD,
                    value="footer",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction):

        selected_option = self.values[0]

        if selected_option == "main":
            form = EmbedBuilderModal(title="Set Embed Title, Description, and Color")
            form.add_item(
                discord.ui.TextInput(
                    label="Title",
                    placeholder="Enter the title of the embed.",
                    max_length=256,
                    required=False,
                    style=discord.TextStyle.short,
                    default=self.view.embed.title,
                )
            )

            form.add_item(
                discord.ui.TextInput(
                    label="Description",
                    placeholder="Enter text for description of embed.",
                    max_length=4000,
                    required=False,
                    style=discord.TextStyle.long,
                    default=self.view.embed.description,
                )
            )

            form.add_item(
                discord.ui.TextInput(
                    label="Color",
                    placeholder="Examples: red, yellow, #00ffb3, etc.",
                    max_length=7,
                    required=False,
                    style=discord.TextStyle.short,
                    default=str(self.view.embed.color.value),
                )
            )

            await interaction.response.send_modal(form)
            await form.wait()

            title, description, color = form.children[0].value, form.children[1].value, form.children[2].value

            self.view.embed.title = title
            self.view.embed.description = description

            try:
                self.view.embed.color = await ColorConverter().convert(self.ctx, color)
            except commands.BadArgument:
                self.view.embed.color = self.view.bot.color

            await self.view.refresh_view()

        elif selected_option == "image":
            form = EmbedBuilderModal(title="Set Embed Images")
            form.add_item(
                discord.ui.TextInput(
                    label="Thumbnail (Small image in right)",
                    placeholder="Enter the URL of the thumbnail image.",
                    required=False,
                    style=discord.TextStyle.short,
                    default=self.view.embed.thumbnail.url,
                )
            )

            form.add_item(
                discord.ui.TextInput(
                    label="Main Image (Large image in center)",
                    placeholder="Enter the URL of the main image.",
                    required=False,
                    style=discord.TextStyle.short,
                    default=self.view.embed.image.url,
                )
            )

            await interaction.response.send_modal(form)
            await form.wait()

            thumbnail, image = form.children[0].value, form.children[1].value

            try:
                self.view.embed.set_thumbnail(url=thumbnail)
            except discord.InvalidArgument:
                self.view.embed.set_thumbnail(url=None)

            try:
                self.view.embed.set_image(url=image)
            except discord.InvalidArgument:
                self.view.embed.set_image(url=None)

            await self.view.refresh_view()

        elif selected_option == "footer":
            form = EmbedBuilderModal(title="Set Embed Footer")
            form.add_item(
                discord.ui.TextInput(
                    label="Footer Text",
                    placeholder="Enter text for footer.",
                    max_length=2048,
                    required=False,
                    style=discord.TextStyle.short,
                    default=self.view.embed.footer.text,
                )
            )

            form.add_item(
                discord.ui.TextInput(
                    label="Footer Icon",
                    placeholder="Enter the image URL of the footer.",
                    required=False,
                    style=discord.TextStyle.short,
                    default=self.view.embed.footer.icon_url,
                )
            )

            await interaction.response.send_modal(form)
            await form.wait()

            text, icon = form.children[0].value, form.children[1].value

            try:
                self.view.embed.set_footer(text=text, icon_url=icon)
            except discord.InvalidArgument:
                self.view.embed.set_footer(text=text, icon_url=None)

            await self.view.refresh_view()
