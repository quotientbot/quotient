from .shards import ShardEvents
from .main import MainEvents


def setup(bot):
    bot.add_cog(ShardEvents(bot))
    bot.add_cog(MainEvents(bot))
