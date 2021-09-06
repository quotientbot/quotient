async def check_member_role(bot, data):
    g_id, m_id, role_id = data["guild_id"], data["member_id"], data["role_id"]

    guild = bot.get_guild(g_id)
    if not guild:
        return {"ok": True, "result": False}

    if not guild.chunked:
        bot.loop.create_task(guild.chunk())

    member = guild.get_member(m_id)
    if not member or not role_id in (role.id for role in member.roles):
        return {"ok": True, "result": False}

    return {"ok": True, "result": True}
