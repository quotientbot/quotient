from discord.ext import commands
import typing

__all__ = ("quocommand", "quogroup")


def quocommand(
    name,
    *,
    perms: typing.Union[str, list, tuple] = "None",
    bot_perms: typing.Union[str, list, tuple] = "Send Messages",
    usage=None,
    examples=None,
    cooldown=0,
    hidden=False,
    disabled=False,
    helpgif=None,
    **kwargs
):

    if isinstance(perms, str):
        perms = [perms]
    if isinstance(bot_perms, str):
        bot_perms = [bot_perms]

    if isinstance(cooldown, (int, float)):
        cooldown = [cooldown, cooldown]

    return commands.command(
        name=name,
        cls=Command,
        perms=perms,
        bot_perms=bot_perms,
        usage=usage,
        helpgif=helpgif,
        examples=examples or [],
        cooldown=cooldown,
        hidden=hidden,
        disabled=disabled,
        **kwargs
    )


def quogroup(
    name,
    *,
    perms: typing.Union[str, list, tuple] = "None",
    helpgif=None,
    bot_perms: typing.Union[str, list, tuple] = "Send Messages",
    examples=None,
    invoke_without_command=False,
    cooldown=0,
    hidden=False,
    disabled=False,
    **kwargs
):

    if isinstance(perms, str):
        perms = [perms]
    if isinstance(bot_perms, str):
        bot_perms = [bot_perms]

    if isinstance(cooldown, (int, float)):
        cooldown = [cooldown, cooldown]

    return commands.group(
        name=name,
        cls=Group,
        perms=perms,
        helpgif=helpgif,
        bot_perms=bot_perms,
        examples=examples or [],
        invoke_without_command=invoke_without_command,
        cooldown=cooldown,
        hidden=hidden,
        disabled=disabled,
        **kwargs
    )


class Command(commands.Command):
    def __init__(self, callback, name, *, perms, bot_perms, examples, helpgif, cooldown, hidden, disabled, **kwargs):
        super().__init__(callback, name=name, hidden=hidden, **kwargs)
        self.perms = perms
        self.helpgif = helpgif
        self.bot_perms = bot_perms
        self.examples = examples
        self.cooldown = cooldown
        self.disabled = disabled


class Group(commands.Group):
    def __init__(self, callback, name, *, helpgif, perms, bot_perms, examples, cooldown, hidden, disabled, **kwargs):
        super().__init__(callback, name=name, hidden=hidden, case_insensitive=True, **kwargs)
        self.perms = perms
        self.bot_perms = bot_perms
        self.helpgif = helpgif
        self.examples = examples
        self.cooldown = cooldown
        self.disabled = disabled

    def command(self, *args, **kwargs):
        def wrapper(func):
            kwargs.setdefault("parent", self)
            result = quocommand(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return wrapper

    def group(self, *args, **kwargs):
        def wrapper(func):
            kwargs.setdefault("parent", self)
            result = quogroup(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return wrapper
