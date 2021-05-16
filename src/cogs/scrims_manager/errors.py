from discord.ext import commands
from core import Cog
import discord


class ScrimError(commands.CommandError):
    pass


class SMError(Cog):
    def __init__(self, bot):
        self.bot = bot

    def red_embed(self, description: str):
        embed = discord.Embed(color=discord.Color.red(), description=description)
        return embed

    @Cog.listener()
    async def on_scrim_registration_deny(self, message, type, scrim):
        logschan = scrim.logschan

        await message.add_reaction("\N{CROSS MARK}")
        e = discord.Embed(
            color=discord.Color.red(),
            description=f"Registraion of [{str(message.author)}]({message.jump_url}) has been denied in {message.channel.mention}\n**Reason:** ",
        )

        if type == "mentioned_bots":
            await message.reply(
                embed=self.red_embed(
                    "Don't mention Bots. Mention your real teammates."
                ),
                delete_after=5,
            )
            e.description += f"Mentioned Bots."

        elif type == "insufficient_mentions":
            await message.reply(
                embed=self.red_embed(
                    f"{str(message.author)}, **`{scrim.required_mentions} mentions`** are required for successful registration."
                ),
                delete_after=5,
            )
            e.description += f"Insufficient Mentions (`{len(message.mentions)}/{scrim.required_mentions}`)"

        elif type == "banned":
            await message.reply(
                embed=self.red_embed(
                    f"{str(message.author)}, You are banned from the scrims. You cannot register."
                ),
                delete_after=5,
            )
            e.description += f"They are banned from scrims."

        if logschan != None and logschan.permissions_for(logschan.guild.me).embed_links:
            await logschan.send(embed=e)
