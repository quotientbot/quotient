from functools import wraps

import discord

from quotient.core.ctx import Context


def role_permissions_check():
    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx: Context, role: discord.Role, *args, **kwargs):
            bot = ctx.guild.me

            # Check if the bot's top role is higher than the role
            if role.position >= bot.top_role.position:
                return await ctx.send(
                    embed=self.bot.error_embed(
                        f"I cannot manage a role ({role.mention}) that is higher than or equal to my highest role ({ctx.guild.me.top_role.mention})."
                    )
                )
            # Check if the user's top role is higher than the role
            if role.position >= ctx.author.top_role.position:
                return await ctx.send(
                    embed=self.bot.error_embed(
                        f"You cannot manage a role ({role.mention}) that is higher than or equal to your highest role ({ctx.interaction.user.top_role.mention})."
                    )
                )

            # Check for harmful permissions
            harmful_permissions = discord.Permissions(
                administrator=True,
                kick_members=True,
                ban_members=True,
                manage_guild=True,
                manage_roles=True,
                manage_channels=True,
                manage_messages=True,
            )
            if any(perm for perm, value in role.permissions if value and getattr(harmful_permissions, perm)):
                return await ctx.send(
                    embed=self.bot.error_embed("This role has potentially harmful permissions and cannot be managed.")
                )

            return await func(self, ctx, role, *args, **kwargs)

        return wrapper

    return decorator
