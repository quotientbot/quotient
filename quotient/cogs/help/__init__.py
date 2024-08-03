from __future__ import annotations

import typing as T

from discord.ext import commands

if T.TYPE_CHECKING:
    from quotient.core.bot import Quotient

import discord

from quotient.cogs.dev.consts import MOD_ROLE_IDS, PRIVATE_GUILD_IDS
from quotient.core.ctx import Context
from quotient.models.others.guild import Guild

HIDDEN_COGS = ("helpcommands", "jishaku", "scrims", "tourney", "devstats")


class HelpCommands(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

        self.bot.remove_command("help")

    async def send_bot_help(self, ctx: Context, g: Guild):
        guild_id = ctx.guild.id
        e = discord.Embed(color=self.bot.color, description="")
        e.set_author(name=ctx.author, icon_url=getattr(ctx.author.avatar, "url", ctx.author.default_avatar.url))
        e.description += (
            f"Hello, I'm {self.bot.user.name}, an [open-source](https://github.com/quotientbot/Quotient-Bot) "
            f"bot made by [dead.dev]({self.bot.config('SUPPORT_SERVER_LINK')}).\n"
            f"- Prefix for this server is: `{g.prefix}`\n"
        )

        for cog_name, cog in self.bot.cogs.items():
            if cog_name in HIDDEN_COGS:
                continue

            if not guild_id in PRIVATE_GUILD_IDS and not any(role_id in MOD_ROLE_IDS for role_id in ctx.author._roles):
                if cog_name == "developer":
                    continue

            app_commands = list(cog.walk_app_commands()) + list(cog.walk_commands())

            if getattr(cog, "SUBCOGS", None):
                for subcog_name in cog.SUBCOGS:
                    subcog = self.bot.get_cog(subcog_name)
                    if subcog:
                        app_commands.extend(subcog.walk_app_commands())

            if not app_commands:
                continue

            cmds_list = ""

            for cmd in app_commands:

                if cmd.parent is None and (isinstance(cmd, commands.HybridCommand) or isinstance(cmd, discord.app_commands.Command)):
                    cmds_list += f"</{cmd.name}:{self.bot.app_commands_global[cmd.name].id}> "
                elif cmd.parent is not None and (
                    isinstance(cmd, commands.HybridCommand) or isinstance(cmd, discord.app_commands.Command)
                ):
                    cmds_list += f"</{cmd.parent.name} {cmd.name}:{self.bot.app_commands_global[cmd.parent.name].id}> "

            e.add_field(name=cog_name.capitalize(), value=cmds_list or "No commands available", inline=False)

        await ctx.send(
            content=self.bot.config("SUPPORT_SERVER_LINK").lstrip("https://"),
            embed=e,
            view=self.bot.contact_support_view(),
        )

    async def send_command_help(self, ctx: Context, command_name: str, g: Guild):
        c = self.bot.get_command(command_name)
        if c is None:
            return await self.send_bot_help(ctx, g)

        e = discord.Embed(color=self.bot.color, description=c.help or "No help found ...")
        e.set_author(name=c.cog_name.capitalize(), icon_url=ctx.guild.me.default_avatar.url)

        if c.name in self.bot.app_commands_global:
            if c.name == "scrims":
                e.add_field(name="Slash Usage", value=f"</{c.name} panel:{self.bot.app_commands_global[c.name].id}>", inline=False)
            else:
                e.add_field(name="Slash Usage", value=f"</{c.name}:{self.bot.app_commands_global[c.name].id}>", inline=False)

        e.add_field(name="Legacy Usage", value=f"`{g.prefix}{c.qualified_name}{c.signature}`", inline=False)

        return await ctx.send(embed=e)

    async def commands_autocomplete(self, inter: discord.Interaction, curr: str) -> list[discord.app_commands.Choice[str]]:
        commands = []

        for cog_name, cog in self.bot.cogs.items():
            if cog_name in HIDDEN_COGS or cog_name == "developer":
                continue

            for cmd in cog.get_commands():
                commands.append(cmd)

        if curr.strip() == "":
            return [discord.app_commands.Choice(name=cmd.name, value=cmd.name) for cmd in commands[:25]]

        return [discord.app_commands.Choice(name=cmd.name, value=cmd.name) for cmd in commands[:25] if curr in cmd.name]

    @commands.hybrid_command("help")
    @commands.guild_only()
    @commands.cooldown(1, 4, commands.BucketType.user)
    @discord.app_commands.describe(command="The command for which you need help")
    @discord.app_commands.autocomplete(command=commands_autocomplete)
    async def help_command(self, ctx: Context, *, command: str = None):
        """Shows help about a command or the bot itself."""

        g = await Guild.get(pk=ctx.guild.id)

        if command == None:
            return await self.send_bot_help(ctx, g)

        return await self.send_command_help(ctx, command, g)


async def setup(bot: Quotient):
    await bot.add_cog(HelpCommands(bot))
