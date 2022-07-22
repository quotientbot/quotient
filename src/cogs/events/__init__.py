from .cmds import CmdEvents
from .errors import Errors
from .main import MainEvents
from .tasks import QuoTasks
from .votes import VotesCog
from .interaction import InteractionErrors


async def setup(bot):
    await bot.add_cog(MainEvents(bot))
    await bot.add_cog(QuoTasks(bot))
    await bot.add_cog(CmdEvents(bot))
    await bot.add_cog(VotesCog(bot))
    await bot.add_cog(Errors(bot))
    await bot.add_cog(InteractionErrors(bot))
