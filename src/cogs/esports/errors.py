import discord
from core import Cog
from models import Scrim
from discord.ext import commands


class ScrimError(commands.CommandError):
    pass

#well yeah the name is SMError but this cog serve much more than just that.

class SMError(Cog):
    def __init__(self, bot):
        self.bot = bot

    def red_embed(self, description: str):
        embed = discord.Embed(color=discord.Color.red(), description=description)
        return embed

    @Cog.listener()
    async def on_scrim_registration_deny(self, message: discord.Message, type: str, scrim: Scrim):
        logschan = scrim.logschan

        await message.add_reaction("\N{CROSS MARK}")
        e = discord.Embed(
            color=discord.Color.red(),
            description=f"Registraion of [{str(message.author)}]({message.jump_url}) has been denied in {message.channel.mention}\n**Reason:** ",
        )

        if type == "mentioned_bots":
            await message.reply(
                embed=self.red_embed("Don't mention Bots. Mention your real teammates."),
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
                embed=self.red_embed(f"{str(message.author)}, You are banned from the scrims. You cannot register."),
                delete_after=5,
            )
            e.description += f"They are banned from scrims."

        if logschan is not None:
            if logschan.permissions_for(logschan.guild.me).embed_links:
                return await logschan.send(embed=e)
            else:
                text = f"I could not send the scrim logs to the logging channel because I don't have the **Embed Links** permission."
                embed=self.red_embed(text)
                return await logschan.send(embed=embed)
            

    @Cog.listener()
    async def on_scrim_log(self, type: str, scrim: Scrim, **kwargs):
        """
        A listener that is dispatched everytime registration starts or ends.
        """
        logschan = scrim.logschan
        role = scrim.role
        scrim_open_role = scrim.open_role
        registration_channel = scrim.registration_channel
        modrole = scrim.modrole

        imp = False
        if type == "open":
            permission_updated = kwargs.get("permission_updated")
            embed = discord.Embed(
                color=0x00B1FF,
                description=f"Registration opened for {scrim_open_role.mention} in {registration_channel.mention}(ScrimsID: `{scrim.id}`)",
            )
            if not permission_updated:
                imp = True
                embed.color = discord.Color.red()
                embed.description += f"\nI couldn't open {registration_channel.mention}."

        elif type == "closed":
            permission_updated = kwargs.get("permission_updated")
            embed = discord.Embed(
                color=discord.Color(0x00B1FF),
                description=f"Registration closed for {scrim_open_role.mention} in {registration_channel.mention}(ScrimsID: `{scrim.id}`)\n\nUse `smanager slotlist {scrim.id} edit` to edit the slotlist.",
            )

            if not permission_updated:
                imp = True
                embed.color = discord.Color.red()
                embed.description += f"\nI couldn't close {registration_channel.mention}."

        elif type == "reg_success":
            message = kwargs.get("message")
            role_added = kwargs.get("role_added")

            embed = discord.Embed(
                color=discord.Color.green(),
                description=f"Registration of [{message.author}]({message.jump_url}) has been accepted in {message.channel.mention}",
            )
            if role_added is False:
                imp = True
                embed.color = discord.Color.red()
                embed.description += f"\nUnfortunately I couldn't give them {role.mention}."

        if logschan != None and logschan.permissions_for(logschan.guild.me).send_messages:
            await logschan.send(
                content=modrole.mention if modrole != None and imp is True else None,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(roles=True),
            )


    @Cog.listener()
    async def on_scrim_cmd_log(self,**kwargs):
        ...
