from enum import Enum

from quotient.models import (
    AutoPurge,
    Guild,
    GuildTier,
    Scrim,
    ScrimReservedSlot,
    ScrimsSlotManager,
    TagCheck,
    Tourney,
    YtNotification,
)


class Feature(Enum):
    """
    Tier wise feature limits.
    -1 means infinite.

    Order: [Free, Starter, Intermediate, Ultimate]
    Features with #limit needs to be checked specifically.
    """

    SCRIM_CREATE = (2, 5, 7, -1)  # limit
    TOURNEY_CREATE = (1, 2, 3, -1)  # limit
    SCRIM_DROP_LOCATION = (0, 1, 1, 1)
    SCRIM_POINTS_TABLE = (0, 0, 1, 1)
    TAG_CHECK_CREATE = (1, 1, 2, -1)  # limit
    EASY_TAG_CREATE = (0, 1, 1, -1)  # limit
    AUTOPURGE_CREATE = (1, 2, 4, -1)  # limit
    YT_NOTI_SETUP = (1, 1, 4, -1)  # limit
    YT_LIVE_NOTI_SETUP = (0, 1, 1, 1)
    CANCEL_CLAIM_PANEL_CREATE = (1, 2, 2, -1)  # limit
    CANCEL_CLAIM_PANEL_REMINDER = (0, 0, 1, 1)
    CUSTOM_REACTIONS_CREATE = (0, 0, 1, 1)
    MAX_SLOT_RESERVATION_PER = (2, 4, 4, -1)  # limit
    MIN_REQ_LINES_TO_REG = (0, 0, 1, 1)
    DUPLICATE_MENTIONS = (0, 0, 0, 1)
    DUPLICATE_TEAMNAME = (0, 0, 1, 1)
    DELETE_EXTRA_REG_SCRIM = (0, 1, 1, 1)
    DELETED_REJECTED_REG = (0, 1, 1, 1)
    REG_END_PING_ROLE_SCRIM = (0, 0, 1, 1)
    CHANNEL_AUTOCLEAN_TIME_SCRIM = (0, 1, 1, 1)
    REG_AUTO_END_TIME_SCRIM = (0, 0, 1, 1)
    SHARE_IDP_CUSTOMIZE_SCRIM = (0, 0, 1, 1)
    SLOTLIST_START_FROM = (0, 0, 1, 1)
    AUTO_SEND_SLOTLIST_TOGGLE_SCRIM = (0, 1, 1, 1)
    SUCCESS_DM_MESSAGE_TOURNEY = (0, 0, 0, 1)
    EXPORT_TOURNEY_TO_EXCEL_TOURNEY = (0, 0, 1, 1)


# TODO: Update checks for EasyTag


async def can_use_feature(feat: Feature, guild_id: int, **kwargs) -> tuple[bool, GuildTier]:
    g = await Guild.get(pk=guild_id)
    tier = g.tier

    if feat == Feature.SCRIM_CREATE:
        scrims_count = await Scrim.filter(guild_id=guild_id).count()
        is_allowed = scrims_count < feat.value[tier.value]
        min_tier = next((t for t, limit in enumerate(feat.value) if limit == -1 or scrims_count < limit), GuildTier.ULTIMATE)
        return is_allowed, GuildTier(min_tier)

    if feat == Feature.TOURNEY_CREATE:
        tourneys_count = await Tourney.filter(guild_id=guild_id).count()
        is_allowed = tourneys_count < feat.value[tier.value]
        min_tier = next((t for t, limit in enumerate(feat.value) if limit == -1 or tourneys_count < limit), GuildTier.ULTIMATE)
        return is_allowed, GuildTier(min_tier)

    if feat == Feature.TAG_CHECK_CREATE:
        tag_checks_count = await TagCheck.filter(guild_id=guild_id).count()
        is_allowed = tag_checks_count < feat.value[tier.value]
        min_tier = next((t for t, limit in enumerate(feat.value) if limit == -1 or tag_checks_count < limit), GuildTier.ULTIMATE)
        return is_allowed, GuildTier(min_tier)

    if feat == Feature.AUTOPURGE_CREATE:
        autopurges_count = await AutoPurge.filter(guild_id=guild_id).count()
        is_allowed = autopurges_count < feat.value[tier.value]
        min_tier = next((t for t, limit in enumerate(feat.value) if limit == -1 or autopurges_count < limit), GuildTier.ULTIMATE)
        return is_allowed, GuildTier(min_tier)

    if feat == Feature.YT_NOTI_SETUP:
        yt_notis_count = await YtNotification.filter(discord_guild_id=guild_id).count()
        is_allowed = yt_notis_count < feat.value[tier.value]
        min_tier = next((t for t, limit in enumerate(feat.value) if limit == -1 or yt_notis_count < limit), GuildTier.ULTIMATE)
        return is_allowed, GuildTier(min_tier)

    if feat == Feature.CANCEL_CLAIM_PANEL_CREATE:
        scrim_slot_manager_count = await ScrimsSlotManager.filter(guild_id=guild_id).count()
        is_allowed = scrim_slot_manager_count < feat.value[tier.value]
        min_tier = next(
            (t for t, limit in enumerate(feat.value) if limit == -1 or scrim_slot_manager_count < limit), GuildTier.ULTIMATE
        )
        return is_allowed, GuildTier(min_tier)

    if feat == Feature.MAX_SLOT_RESERVATION_PER:
        scrim_id = kwargs.get("scrim_id")
        reserved_slots_count = await ScrimReservedSlot.filter(scrim=await Scrim.get(pk=scrim_id)).count()
        is_allowed = reserved_slots_count < feat.value[tier.value]
        min_tier = next((t for t, limit in enumerate(feat.value) if limit == -1 or reserved_slots_count < limit), GuildTier.ULTIMATE)
        return is_allowed, GuildTier(min_tier)

    is_allowed = feat.value[tier.value]
    min_tier = next((t for t, limit in enumerate(feat.value) if limit == -1 or limit > 0), GuildTier.ULTIMATE)
    return is_allowed, GuildTier(min_tier)
