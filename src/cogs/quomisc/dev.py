from core import Cog, Quotient, Context
from discord.ext import commands
import sys, importlib, os, re
from utils import emote
import subprocess
import asyncio

__all__ = ("Dev",)


class Dev(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    def cog_check(self, ctx):
        return ctx.author.id in ctx.config.DEVS

    async def run_process(self, command):
        try:
            process = await asyncio.create_subprocess_shell(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await process.communicate()
        except NotImplementedError:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await self.bot.loop.run_in_executor(None, process.communicate)

        return [output.decode() for output in result]

    _GIT_PULL_REGEX = re.compile(r"\s*(?P<filename>.+?)\s*\|\s*[0-9]+\s*[+-]+")

    def find_modules_from_git(self, output):
        files = self._GIT_PULL_REGEX.findall(output)
        ret = []
        for file in files:
            root, ext = os.path.splitext(file)
            if ext != ".py":
                continue

            if root.startswith("cogs/"):
                ret.append((root.count("/") - 1, root.replace("/", ".")))

        # For reload order, the submodules should be reloaded first
        ret.sort(reverse=True)
        return ret

    def reload_or_load_extension(self, module):
        try:
            self.bot.reload_extension(module)
        except commands.ExtensionNotLoaded:
            self.bot.load_extension(module)

    @commands.command(hidden=True)
    async def sync(self, ctx: Context):
        """Reloads all modules, while pulling from git."""

        async with ctx.typing():
            stdout, stderr = await self.run_process("git pull")
        if stdout.startswith("Already up to date."):
            return await ctx.send(stdout)

        modules = self.find_modules_from_git(stdout)
        mods_text = "\n".join(f"{index}. `{module}`" for index, (_, module) in enumerate(modules, start=1))
        prompt_text = f"This will update the following modules, are you sure?\n{mods_text}"
        confirm = await ctx.prompt(prompt_text)
        if not confirm:
            return await ctx.send("Aborting.")

        statuses = []
        for is_submodule, module in modules:
            if is_submodule:
                try:
                    actual_module = sys.modules[module]
                except KeyError:
                    statuses.append((emote.error, module))
                else:
                    try:
                        importlib.reload(actual_module)
                    except Exception as e:
                        statuses.append((emote.xmark, module))
                    else:
                        statuses.append((emote.check, module))
            else:
                try:
                    self.reload_or_load_extension(module)
                except commands.ExtensionError:
                    statuses.append((emote.xmark, module))
                else:
                    statuses.append((emote.check, module))

        await ctx.send("\n".join(f"{status}: `{module}`" for status, module in statuses))
