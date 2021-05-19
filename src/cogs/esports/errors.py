import discord
from core import Cog
from discord.ext import commands
from models import Scrim, Timer, BannedTeam, ReservedSlot


class ScrimError(commands.CommandError):
    pass


# well yeah the name is SMError but this cog serve much more than just that.


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
                # The bot will not be able to send embeds to this channel because of lack of permission.
                text = f"I could not send the scrim logs to the logging channel because I don't have the **Embed Links** permission."
                embed = self.red_embed(text)
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
        else:
            text = f"I could not send the scrim logs to the logging channel because I don't have the **Embed Links** permission."
            return await logschan.send(text)

    @Cog.listener()
    async def on_scrim_unban_timer_complete(self, timer: Timer):
        scrim_id = timer.kwargs["scrim_id"]
        user_id = timer.kwargs["user_id"]
        banned_by = timer.kwargs["banned_by"]

        scrim = await Scrim.get_or_none(pk=scrim_id)
        if scrim is None:
            # probably deleted
            await scrim.delete()

        guild = scrim.guild
        if guild is None:  # sed
            await scrim.delete()

        if not user_id in await scrim.banned_user_ids():
            # probably unbanned manually with the command.
            return

        ban = await scrim.banned_teams.filter(user_id=user_id).first()
        await BannedTeam.filter(id=ban.id).delete()

        logschan = scrim.logschan
        if logschan is not None and logschan.permissions_for(guild.me).send_messages:
            banner = guild.get_member(banned_by) or self.bot.get_user(banned_by)
            user = guild.get_member(user_id) or self.bot.get_user(user_id)
            embed = discord.Embed(
                color=discord.Color.green(),
                description=f"{user} ({user_id}) have been unbanned from Scrim (`{scrim.id}`).\nThey were banned by {banner} ({banned_by}).",
            )
            await logschan.send(embed=embed)

    @Cog.listener()
    async def on_scrim_reserve_timer_complete(self, timer: Timer):
        scrim_id = timer.kwargs["scrim_id"]
        team_name = timer.kwargs["team_name"]
        user_id = timer.kwargs["user_id"]

        scrim = await Scrim.get_or_none(pk=scrim_id)
        if scrim is None:
            await scrim.delete()

        guild = scrim.guild
        if not guild:
            await scrim.delete()

        if not user_id in await scrim.reserved_user_ids():
            return

        team = await scrim.reserved_slots.filter(user_id=user_id).first()
        await ReservedSlot.filter(id=team.id).delete()

        logschan = scrim.logschan
        if logschan is not None and logschan.permissions_for(guild.me).send_messages:
            user = self.bot.get_user(user_id)
            embed = discord.Embed(
                color=discord.Color.green(),
                description=f"Reservation period of **{team_name.title()}** ({user}) is now over.\nSlot will not be reserved for them in Scrim (`{scrim_id}`).",
            )

            await logschan.send(embed=embed)

    @Cog.listener()
    async def on_scrim_cmd_log(self, **kwargs):
        ...
