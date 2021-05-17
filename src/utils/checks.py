from discord.ext import commands


class SMNotUsable(commands.CheckFailure):
    pass


def can_use_sm():  # basic check
    async def predicate(ctx):
        if ctx.author.guild_permissions.manage_guild or 'scrims-mod' in [role.name.lower() for role in ctx.author.roles]:
            return True
        else:
            raise SMNotUsable()

    return commands.check(predicate)