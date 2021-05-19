from discord.ext import commands

class ShardEvents(commands.Cog, name="Shard Events"):
    """
    Events triggered on shard activities.
    Since the bot is seeing >2000 guilds now,
    this seems necessary.
    """
    def __init__(self, bot):
        self.bot = bot
        
    # TODO: Add functionality to the events.
    # TODO: Add ability to send webhooks on shard death and reconnection.
        
    @commands.Cog.listener()
    async def on_shard_ready(self, shard_id):
        ...
        
    @commands.Cog.listener()
    async def on_shard_resumed(self, shard_id):
        ...
        
    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard_id):
        ...
        
def setup(bot):
    bot.add_cog(ShardEvents(bot))