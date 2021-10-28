from aiohttp import ClientSession
from utils import emote
import discord
import io


class PremiumView(discord.ui.View):
    def __init__(self, text="*This feature requires you to have Quotient Premium.*"):
        super().__init__(timeout=None)
        self.text = text
        self.add_item(
            discord.ui.Button(url="https://quotientbot.xyz/premium/buy", emoji=emote.diamond, label="Try Premium")
        )

    @property
    def premium_embed(self) -> discord.Embed:
        _e = discord.Embed(
            color=discord.Color.gold(), description=f"**You discovered a premium feature <a:premium:807911675981201459>**"
        )

        _e.description += (
            f"\n{self.text}\n\n**Quotient Premium includes:**\n"
            "- Host Unlimited Scrims and Tournaments.\n"
            "- Unlimited tagcheck and easytag channels.\n"
            "- Custom footer and color of all embeds bot sends.\n"
            "- Custom reactions for tourney and scrims.\n"
            "- Unlimited ssverification and media partner channels.\n"
            "- Premium role in our server and 10+ other benefits..."
        )
        _e.set_image(url="https://cdn.discordapp.com/attachments/851846932593770496/901494096579936318/premium.png")
        # _e.set_footer(text="Buy Premium and I'll love you even more - deadshot#7999")
        return _e


class PremiumActivate(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        url = "https://discord.com/oauth2/authorize?client_id={0}&scope=applications.commands%20bot&permissions=21175985838&guild_id={1}"
        _options = [
            discord.ui.Button(url=url.format(846339012607082506, guild_id), emoji="<:redquo:902966581951344672>"),
            discord.ui.Button(url=url.format(846339012607082506, guild_id), emoji="<:whitequo:902966576800731147>"),
            discord.ui.Button(url=url.format(846339012607082506, guild_id), emoji="<:greenquo:902966579711578192>"),
            discord.ui.Button(url=url.format(846339012607082506, guild_id), emoji="<:purplequo:902966579812237383>"),
            discord.ui.Button(url=url.format(846339012607082506, guild_id), emoji="<:orangequo:902966579938099200>"),
        ]
        for _item in _options:
            self.add_item(_item)

    @property
    def initial_message(self):
        return "Choose your Color and Invite it\n" "**Type `activate @Quotient` when you have it in the server.**\n"

    @property
    async def image(self):
        async with ClientSession() as session:
            async with session.get(
                "https://cdn.discordapp.com/attachments/829953427336593429/903303537302319144/all_pre.png"
            ) as res:
                invert = io.BytesIO(await res.read())
                return discord.File(invert, "premium.png")
