from .idp import IdpIpc
from .scrim import ScrimIpc
from .ssverify import SSverifyIpc
from .settings import SettingsIpc
from .partners import QuoPartners


def setup(bot):
    bot.add_cog(IdpIpc(bot))
    bot.add_cog(ScrimIpc(bot))
    bot.add_cog(SSverifyIpc(bot))
    bot.add_cog(SettingsIpc(bot))
    bot.add_cog(QuoPartners(bot))
