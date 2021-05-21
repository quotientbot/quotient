from .functions import *
import discord, config
from utils import Pages

from core import Cog, Quotient
from discord.ext import commands
from difflib import get_close_matches


class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={
                "cooldown": commands.Cooldown(1, 3.0, commands.BucketType.member),
                "help": "Shows help about the bot, a command, or a category",
            }
        )

    async def send_bot_help(self, mapping):
        ctx = self.context
        cats = []

        hidden = ("HelpCog",)
        for cog, cmds in mapping.items():
            if cog and not cog.qualified_name in hidden:
                if await self.filter_commands(cmds, sort=True):
                    cats.append(cog)

        embed = discord.Embed(color=discord.Color(config.COLOR))
        for idx in cats:
            embed.add_field(
                inline=False,
                name=idx.qualified_name.title(),
                value=", ".join(map(lambda x: f"`{x}`", idx.get_commands())),
            )

        cmds = sum(1 for i in self.context.bot.walk_commands())

        embed.set_footer(text="Total Commands: {}".format(cmds))
        await ctx.send(embed=embed)

    async def send_group_help(self, group):
        if not group.commands:
            return await self.send_command_help(group)

        embed = discord.Embed(color=discord.Color(config.COLOR))

        embed.title = f"{group.qualified_name} {group.signature}"
        _help = group.help or "No description provided"
        embed.description = f"> {_help}"
        embed.set_footer(text=f'Use "{self.clean_prefix}help <command>" for more information.')
        embed.add_field(
            name="Subcommands",
            value="\n".join(f"`{self.clean_prefix}{c.qualified_name}` : {c.short_doc}" for c in group.commands),
        )
        if group.aliases:
            embed.add_field(name="Aliases", value=", ".join(f"`{aliases}`" for aliases in group.aliases), inline=False)
        await self.context.send(embed=embed)

    async def send_cog_help(self, cog):
        commands = []
        c = 0
        for cmd in cog.get_commands():
            if cmd.hidden:
                continue

            if cmd.short_doc is None:
                brief = "No information."
            else:
                brief = cmd.short_doc

            if not cmd.hidden:
                c += 1
            commands.append(f"`{cmd.qualified_name}` - {brief}\n")

        paginator = Pages(
            self.context,
            title=f"{cog.qualified_name.title()} ({c})",
            entries=commands,
            per_page=12,
            show_entry_count=False,
            author=self.context.author,
        )

        await paginator.paginate()

    async def send_command_help(self, command):
        embed = discord.Embed(colour=discord.Colour(config.COLOR))
        common_command_formatting(self, embed, command)
        await self.context.send(embed=embed)

    async def command_not_found(self, string: str):
        message = f"Could not find the `{string}` command. "
        commands_list = [str(cmd) for cmd in self.context.bot.walk_commands()]

        if dym := "\n".join(get_close_matches(string, commands_list)):
            message += f"Did you mean...\n{dym}"

        return message


class HelpCog(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.old_help_command = bot.help_command
        bot.help_command = HelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.old_help_command


def setup(bot):
    bot.add_cog(HelpCog(bot))
