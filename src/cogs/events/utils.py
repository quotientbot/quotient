from models import *


async def erase_guild(guild_id: int):
    check = await Guild.get_or_none(guild_id=guild_id)
    if check and not check.is_premium:
        await Guild.filter(guild_id=guild_id).delete()

    scrims = await Scrim.filter(guild_id=guild_id)

    await Scrim.filter(pk__in=(scrim.id for scrim in scrims)).delete()

    await Tourney.filter(guild_id=guild_id).delete()
    await Autorole.filter(guild_id=guild_id).delete()
    await Tag.filter(guild_id=guild_id).delete()
    await Lockdown.filter(guild_id=guild_id).delete()
    await Autoevent.filter(guild_id=guild_id).delete()
    await Giveaway.filter(guild_id=guild_id).delete()
    await Partner.filter(guild_id=guild_id).delete()
    await AutoPurge.filter(guild_id=guild_id).delete()
    await SlotManager.filter(guild_id=guild_id).delete()
    await SlotLocks.filter(pk__in=(scrim.id for scrim in scrims)).delete()
    await EasyTag.filter(guild_id=guild_id).delete()
    await TagCheck.filter(guild_id=guild_id).delete()
