from core import Cog, Quotient
from colorama import Fore, Style, init

init(autoreset=True)


class ShardEvents(Cog, name="Shard Events"):
    """
    Events triggered on shard activities.
    Since the bot is seeing >2000 guilds now,
    this seems necessary.
    """

    def __init__(self, bot: Quotient):
        self.bot = bot

    # TODO: shard events should also be sent as a webhook to the server to prevent checking terminal.
    # FIXME: Pyaare colors not showing up. @deadshot

    @Cog.listener()
    async def on_shard_ready(self, shard_id):
        print(Style.BRIGHT + f"Launched shard #{shard_id}.")

    @Cog.listener()
    async def on_shard_resumed(self, shard_id):
        print(Style.BRIGHT + f"Reconnected shard #{shard_id}.")

    @Cog.listener()
    async def on_shard_disconnect(self, shard_id):
        print(Fore.RED + f"Shard #{shard_id} died.")
