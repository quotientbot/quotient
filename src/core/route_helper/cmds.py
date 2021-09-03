from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from .utils import deny_request
from dataclasses import dataclass, asdict


@dataclass
class Module:
    name: str
    cmds: typing.List[Command]


@dataclass
class Command:
    name: str
    usage: str
    short_doc: str = "No help found..."
    description: str = "No help found..."


async def get_commands(bot: Quotient) -> list:
    _list = []

    for cog, cmds in bot.cogs.items():
        if cog not in ("HelpCog", "Dev", "jishaku") and (cmds := cmds.get_commands()):
            _cmds = []
            for cmd in cmds:
                usage = f"{cmd.qualified_name} {cmd.signature}".strip()
                _cmds.append(Command(cmd.name, usage, cmd.short_doc, cmd.help))

            _list.append(asdict(Module(cog.title(), _cmds)))

    return {"ok": True, "data": _list}
