from .shards import ShardEvents
from .main import MainEvents
from .tasks import QuoTasks
from .cmds import CmdEvents


def setup(bot):
    bot.add_cog(ShardEvents(bot))
    bot.add_cog(MainEvents(bot))
    bot.add_cog(QuoTasks(bot))
    bot.add_cog(CmdEvents(bot))
