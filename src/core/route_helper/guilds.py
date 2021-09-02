from models import Guild


async def update_guild_cache(bot, guild_id: int):
    guild = await Guild.get(guild_id=int(guild_id))

    bot.guild_data[guild.guild_id] = {
        "prefix": guild.prefix,
        "color": guild.embed_color,
        "footer": guild.embed_footer,
    }

    return {"ok": True, "result": {}, "error": None}
