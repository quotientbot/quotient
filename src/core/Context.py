from discord.ext import commands
import discord, asyncio
import utils, io


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pool = self.bot.db

    @property
    def db(self):
        return self.pool

    @property
    def session(self):
        return self.bot.session

    @property
    def config(self):
        return self.bot.config

    @discord.utils.cached_property
    def replied_reference(self):
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved.to_reference()
        return None

    async def prompt(
        self,
        message,
        title=None,
        timeout=60.0,
        delete_after=True,
        author_id=None,
    ):
        """
        An interactive reaction confirmation dialog.
        """

        if not self.channel.permissions_for(self.me).add_reactions:
            raise RuntimeError("Bot does not have Add Reactions permission.")

        fmt = f"**{message}**\n\nReact with \N{WHITE HEAVY CHECK MARK} to confirm or \N{CROSS MARK} to deny."
        embed = discord.Embed(description=fmt, color=self.config.COLOR)
        if title != None:
            embed.title = title
        author_id = author_id or self.author.id
        msg = await self.send(embed=embed)

        confirm = None

        def check(payload):
            nonlocal confirm

            if payload.message_id != msg.id or payload.user_id != author_id:
                return False

            codepoint = str(payload.emoji)

            if codepoint == "\N{WHITE HEAVY CHECK MARK}":
                confirm = True
                return True
            elif codepoint == "\N{CROSS MARK}":
                confirm = False
                return True

            return False

        for emoji in ("\N{WHITE HEAVY CHECK MARK}", "\N{CROSS MARK}"):
            await msg.add_reaction(emoji)

        try:
            await self.bot.wait_for("raw_reaction_add", check=check, timeout=timeout)
        except asyncio.TimeoutError:
            confirm = None

        try:
            if delete_after:
                await msg.delete()
        finally:
            return confirm

    async def error(self, message, delete_after=None):
        return await self.send(
            embed=discord.Embed(description=message, color=discord.Color.red()),
            delete_after=delete_after,
        )

    async def success(self, message, delete_after=None):
        return await self.send(
            embed=discord.Embed(
                description=f"{utils.check} | {message}",
                color=self.config.COLOR,
            ),
        )

    async def send_file(self, content, *, name: str = "Message.txt", escape_mentions=True, **kwargs):
        """
        sends the file containg content
        """
        if escape_mentions:
            content = discord.utils.escape_mentions(content)

        fp = io.BytesIO(content.encode())
        kwargs.pop("file", None)

        return await self.send(file=discord.File(fp, filename=name), **kwargs)
