from .cmds import CmdEvents
from .errors import Errors
from .main import MainEvents
from .tasks import QuoTasks
from .votes import VotesCog


def setup(bot):
    bot.add_cog(MainEvents(bot))
    bot.add_cog(QuoTasks(bot))
    bot.add_cog(CmdEvents(bot))
    bot.add_cog(VotesCog(bot))
    bot.add_cog(Errors(bot))
