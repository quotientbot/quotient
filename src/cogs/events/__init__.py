from .shards import ShardEvents
from .main import MainEvents
from .tasks import QuoTasks


def setup(bot):
    bot.add_cog(ShardEvents(bot))
    bot.add_cog(MainEvents(bot))
    bot.add_cog(QuoTasks(bot))
