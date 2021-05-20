from core import Cog, Quotient
from colorama import Fore, Style, init
from discord_webhook import DiscordWebhook
from utils import emote
import config

init(autoreset=True)


class ShardEvents(Cog, name="Shard Events"):
    """
    Events triggered on shard activities.
    Since the bot is seeing >2000 guilds now,
    this seems necessary.
    """

    def __init__(self, bot: Quotient):
        self.bot = bot


    @Cog.listener()
    async def on_shard_ready(self, shard_id):
        print(Fore.GREEN + f"Launched shard #{shard_id}.")
        webhook = DiscordWebhook(url=config.SHARD_LOG, content=f'{emote.check} Launched shard #{shard_id} | Total Shards: {len(self.bot.shards)}.')
        webhook.execute()

    @Cog.listener()
    async def on_shard_resumed(self, shard_id):
        print(Fore.GREEN + f"Reconnected shard #{shard_id}.")
        webhook = DiscordWebhook(url=config.SHARD_LOG, content=f'{emote.check} Reconnected shard #{shard_id}.')
        webhook.execute()

    @Cog.listener()
    async def on_shard_disconnect(self, shard_id):
        print(Fore.RED + f"Shard #{shard_id} died.")
        webhook = DiscordWebhook(url=config.SHARD_LOG, content=f'{emote.error} Shard #{shard_id} died.')
        webhook.execute()
