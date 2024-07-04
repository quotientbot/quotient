import os

import discord


def default_reg_open_msg() -> discord.Embed:
    """
    Returns the default embed message for the registration open message.
    """
    return discord.Embed(
        color=int(os.getenv("DEFAULT_COLOR")),
        title="Registration is now open!",
        description="📣 **`<<mentions>>`** mentions required.\n📣 Total slots: **`<<slots>>`** [`<<reserved>>` slots reserved]",
    )


def default_reg_close_msg() -> discord.Embed:
    """
    Returns the default embed message for the registration close message.
    """
    return discord.Embed(color=int(os.getenv("DEFAULT_COLOR")), description="**Registration is now Closed!**")


def default_slotlist_msg() -> discord.Embed:
    """
    Returns the default embed message scrims slotlist.
    """
    return discord.Embed(
        color=int(os.getenv("DEFAULT_COLOR")),
        title=f"#<<name>> Slotlist",
        description="```\n<<slots>>\n```",
    ).set_footer(text=f"Registration took: <<time_taken>>")
