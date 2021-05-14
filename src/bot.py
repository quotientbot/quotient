from discord import AllowedMentions, Intents
from colorama import Fore
from core import Quotient
import os, traceback

intents = Intents.default()
intents.members = True

bot = Quotient(
    intents=intents,
    max_messages=1000,
    strip_after_prefix=True,
    case_insensitive=True,
    chunk_guilds_at_startup=False,
    allowed_mentions=AllowedMentions(
        everyone=False, roles=False, replied_user=True, users=True
    ),
)

os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
print(Fore.RED + "-----------------------------------------------------")


for ext in bot.config.EXTENSIONS:
    try:
        bot.load_extension(ext)
        print(Fore.YELLOW + f"[EXTENSION] {ext} was loaded successfully!")
    except Exception as e:
        tb = traceback.format_exception(type(e), e, e.__traceback__)
        tbe = "".join(tb) + ""
        print(Fore.RED + f"[WARNING] Could not load extension {ext}: {tbe}")


@bot.before_invoke
async def bot_before_invoke(ctx):
    if ctx.guild is not None:
        if not ctx.guild.chunked:
            await ctx.guild.chunk()


if __name__ == "__main__":
    bot.run(bot.config.DISCORD_TOKEN, reconnect=True)
