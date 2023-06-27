from .cmds import CmdEvents
from .errors import Errors
from .interaction import InteractionErrors
from .logs import LogEvents
from .main import MainEvents
from .tasks import QuoTasks
from .votes import VotesCog
from .interaction import InteractionErrors
from .pro_checks import ProCheckEvents


async def setup(bot):
    await bot.add_cog(MainEvents(bot))
    await bot.add_cog(QuoTasks(bot))
    await bot.add_cog(CmdEvents(bot))
    await bot.add_cog(Errors(bot))
    await bot.add_cog(InteractionErrors(bot))

    from core import Quotient

    if Quotient.is_pro_bot():
        await bot.add_cog(ProCheckEvents(bot))

    else:
        await bot.add_cog(VotesCog(bot))
    await bot.add_cog(LogEvents(bot))
