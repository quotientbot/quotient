from contextlib import suppress
from models import Autorole, ArrayRemove
from core import Cog, Quotient, Context
import discord


class CmdEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    async def bot_check(self, ctx: Context):
        if ctx.author.id in ctx.config.DEVS:
            return True

        if self.bot.lockdown == True:
            return False

        if not ctx.guild:
            return False

        return True

    @Cog.listener()
    async def on_command(self, ctx: Context):
        if ctx.command.parent:
            cmd = f"{ctx.command.parent} {ctx.command.name}"
        else:
            cmd = ctx.command.name

        record = await ctx.db.fetchval(
            "SELECT uses FROM cmd_stats WHERE guild_id = $1 AND user_id = $2 AND cmd = $3 ",
            ctx.guild.id,
            ctx.author.id,
            cmd,
        )
        if record:
            await ctx.db.execute(
                "UPDATE cmd_stats SET uses = uses + 1 WHERE guild_id = $1 AND user_id = $2 AND cmd = $3",
                ctx.guild.id,
                ctx.author.id,
                cmd,
            )
        else:
            await ctx.db.execute(
                "INSERT INTO cmd_stats (guild_id , user_id , cmd , uses) VALUES ($1, $2, $3, $4) ",
                ctx.guild.id,
                ctx.author.id,
                cmd,
                1,
            )

    @Cog.listener(name="on_member_join")
    async def on_autorole(self, member: discord.Member):
        guild = member.guild

        with suppress(discord.HTTPException):
            record = await Autorole.get_or_none(guild_id=guild.id)
            if not record:
                return

            elif not member.bot and len(record.humans):
                for role in record.humans:
                    try:
                        await member.add_roles(discord.Object(id=role), reason="Quotient's autorole")
                    except (discord.NotFound, discord.Forbidden):
                        await Autorole.filter(guild_id=guild.id).update(humans=ArrayRemove("humans", role))
                        continue

            elif member.bot and len(record.bots):
                for role in record.bots:
                    try:
                        await member.add_roles(discord.Object(id=role), reason="Quotient's autorole")
                    except (discord.Forbidden, discord.NotFound):
                        await Autorole.filter(guild_id=guild.id).update(bots=ArrayRemove("bots", role))
                        continue
            else:
                return
