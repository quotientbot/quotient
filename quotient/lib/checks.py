import discord


def role_has_harmful_permissions(role: discord.Role) -> bool:
    harmful_permissions = [
        "kick_members",
        "ban_members",
        "administrator",
        "manage_guild",
        "manage_channels",
        "manage_messages",
        "manage_roles",
        "manage_webhooks",
        "manage_emojis",
        "view_audit_log",
        "manage_threads",
        "manage_emojis_and_stickers",
    ]

    # Check if any of the harmful permissions are set to True in the role's permissions
    return any(getattr(role.permissions, perm) for perm in harmful_permissions)
