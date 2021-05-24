from collections import Counter
import discord


async def _self_clean_system(ctx, search) -> dict:
    count = 0
    async for msg in ctx.history(limit=search, before=ctx.message):
        if msg.author == ctx.me:
            await msg.delete()
            count += 1
    return {"Bot": count}


async def _complex_cleanup_strategy(ctx, search) -> Counter:
    def check(m):
        return m.author == ctx.me or m.content.startswith(ctx.prefix)

    deleted = await ctx.channel.purge(limit=search, check=check, before=ctx.message)
    return Counter(m.author.display_name for m in deleted)


async def role_checker(ctx, role):
    if role.managed:
        await ctx.error(f"Role is an integrated role and cannot be added manually.")
        return False
    elif ctx.me.top_role.position <= role.position:
        await ctx.error(f"The position of {role.mention} is above my toprole ({ctx.me.top_role.mention})")
        return False
    elif not ctx.author == ctx.guild.owner and ctx.author.top_role.position <= role.position:
        await ctx.error(f"The position of {role.mention} is above your top role ({ctx.author.top_role.mention})")
        return False

    else:
        return True


async def do_removal(ctx, limit, predicate, *, before=None, after=None):
    if limit > 2000:
        return await ctx.error(f"Too many messages to search given ({limit}/2000)")

    if before is None:
        before = ctx.message
    else:
        before = discord.Object(id=before)

    if after is not None:
        after = discord.Object(id=after)

    try:
        deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
    except discord.Forbidden as e:
        return await ctx.error("I do not have permissions to delete messages.")
    except discord.HTTPException as e:
        return await ctx.error(f"Error: {e} (try a smaller search?)")

    spammers = Counter(m.author.display_name for m in deleted)
    deleted = len(deleted)
    messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
    if deleted:
        messages.append("")
        spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
        messages.extend(f"**{name}**: {count}" for name, count in spammers)

    to_send = "\n".join(messages)

    if len(to_send) > 2000:
        await ctx.send(f"Successfully removed {deleted} messages.", delete_after=10)
    else:
        await ctx.send(to_send, delete_after=10)
