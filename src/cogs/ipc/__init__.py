# from __future__ import annotations

from .idp import IdpIpc
from .scrim import ScrimIpc
from .ssverify import SSverifyIpc


def setup(bot):
    bot.add_cog(IdpIpc(bot))
    bot.add_cog(ScrimIpc(bot))
    bot.add_cog(SSverifyIpc(bot))
