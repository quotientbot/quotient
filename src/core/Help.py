from difflib import get_close_matches
from discord.ext import commands
from utils import get_ipm, QuoPaginator, truncate_string, LinkType, LinkButton
import discord


class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            verify_checks=False,
            command_attrs={
                "help": "Shows help about the bot, a command, or a category",
            },
        )

    @property
    def color(self):
        return self.context.config.COLOR

    @property
    def config(self):
        return self.context.bot.config

    async def send_bot_help(self, mapping):
        ctx = self.context

        hidden = ("HelpCog", "Dev")

        embed = discord.Embed(color=self.color)
        server = f"[Support Server]({self.config.SERVER_LINK})"
        invite = f"[Invite Me]({self.config.BOT_INVITE})"
        src = f"[Source]({self.config.REPOSITORY})"
        dashboard = f"[Dashboard]({self.config.WEBSITE})"
        donate = f"[Donate]({self.config.DONATE_LINK})"

        embed.description = f"{server} **|** {invite} **|** {src} **|** {dashboard} **|** {donate}"

        for cog, cmds in mapping.items():
            if cog and not cog.qualified_name in hidden and await self.filter_commands(cmds, sort=True):
                embed.add_field(
                    inline=False,
                    name=cog.qualified_name.title(),
                    value=", ".join(map(lambda x: f"`{x}`", cog.get_commands())),
                )

        cmds = sum(1 for i in self.context.bot.walk_commands())

        embed.set_footer(text="Total Commands: {}  | Invoke rate per minute: {}".format(cmds, round(get_ipm(ctx.bot), 2)))

        links = [LinkType("Support Server", self.config.SERVER_LINK), LinkType("Invite Me", self.config.BOT_INVITE)]
        await ctx.send(embed=embed, embed_perms=True, view=LinkButton(links))

    async def send_group_help(self, group):
        prefix = self.context.prefix

        if not group.commands:
            return await self.send_command_help(group)

        embed = discord.Embed(color=discord.Color(self.color))

        embed.title = f"{group.qualified_name} {group.signature}"
        _help = group.help or "No description provided..."

        _cmds = "\n".join(f"`{prefix}{c.qualified_name}` : {truncate_string(c.short_doc,60)}" for c in group.commands)

        embed.description = f"> {_help}\n\n**Subcommands**\n{_cmds}"

        embed.set_footer(text=f'Use "{prefix}help <command>" for more information.')
        if group.aliases:
            embed.add_field(name="Aliases", value=", ".join(f"`{aliases}`" for aliases in group.aliases), inline=False)
        await self.context.send(embed=embed, embed_perms=True)

    async def send_cog_help(self, cog):
        paginator = QuoPaginator(self.context, per_page=14)
        c = 0
        for cmd in cog.get_commands():
            if not cmd.hidden:
                _brief = "No Information..." if not cmd.short_doc else truncate_string(cmd.short_doc, 60)
                paginator.add_line(f"`{cmd.qualified_name}` : {_brief}")
                c += 1

        paginator.title = f"{cog.qualified_name.title()} ({c})"
        await paginator.start()

    async def send_command_help(self, cmd):
        embed = discord.Embed(color=self.color)
        embed.title = cmd.qualified_name
        embed.description = cmd.help or "No help found..."

        embed.add_field(name="**Usage** ", value=f"`{self.get_command_signature(cmd)}`")
        if cmd.aliases:
            embed.add_field(name="Aliases", value=", ".join((f"`{alias}`" for alias in cmd.aliases)))

        if cmd.extras:
            if _gif := cmd.extras.get("gif"):
                embed.set_image(url=_gif)

        await self.context.send(embed=embed, embed_perms=True)

    async def command_not_found(self, string: str):
        message = f"Could not find the `{string}` command. "
        commands_list = (str(cmd) for cmd in self.context.bot.walk_commands())

        if dym := "\n".join(get_close_matches(string, commands_list)):
            message += f"Did you mean...\n{dym}"

        return message
