from core import Cog, Quotient


class ShardEvents(Cog, name="Shard Events"):
    """
    Events triggered on shard activities.
    Since the bot is seeing >2000 guilds now,
    this seems necessary.
    """

    def __init__(self, bot: Quotient):
        self.bot = bot

    # TODO: Add functionality to the events.
    # TODO: Add ability to send webhooks on shard death and reconnection.

    @Cog.listener()
    async def on_shard_ready(self, shard_id):
        ...

    @Cog.listener()
    async def on_shard_resumed(self, shard_id):
        ...

    @Cog.listener()
    async def on_shard_disconnect(self, shard_id):
        ...
