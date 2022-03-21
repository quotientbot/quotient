from aiohttp import ClientSession
from utils import emote
from typing import List

import discord
import config
import io


class PremiumView(discord.ui.View):
    def __init__(self, text="*This feature requires you to have Quotient Premium.*", *, label="Try Premium"):
        super().__init__(timeout=None)
        self.text = text
        self.add_item(
            discord.ui.Button(
                url="https://quotientbot.xyz/premium",
                emoji=emote.diamond,
                label=label,
            )
        )

    @property
    def premium_embed(self) -> discord.Embed:
        _e = discord.Embed(
            color=0x00FFB3, description=f"**You discovered a premium feature <a:premium:807911675981201459>**"
        )

        _e.description += f"\n`{self.text}`"  # `\n\n**Quotient Premium includes:**\n"
        #     "- Host Unlimited Scrims and Tournaments.\n"
        #     "- Add unlimited slot-manager channels. (`cancel-claim`)\n"
        #     "- Unlimited tagcheck and easytag channels.\n"
        #     "- Custom footer and color of all embeds bot sends.\n"
        #     "- Custom reactions for tourney and scrims.\n"
        #     "- Unlimited ssverification channels. (`youtube/insta`)\n"
        #     "- Unlimited media partner channels.\n"
        #     "- Premium role in our server and other benefits..."
        #
        _e.set_image(
            url="https://cdn.discordapp.com/attachments/782161513825042462/933027639013289984/QUOTIENT-PERKS.png"
        )
        return _e


class PremiumActivate(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        url = "https://discord.com/oauth2/authorize?client_id={0}&scope=applications.commands%20bot&permissions=21175985838&guild_id={1}"
        _options = [
            discord.ui.Button(url=url.format(902856923311919104, guild_id), emoji="<:redquo:902966581951344672>"),
            discord.ui.Button(url=url.format(902857418390765569, guild_id), emoji="<:whitequo:902966576800731147>"),
            discord.ui.Button(url=url.format(846339012607082506, guild_id), emoji="<:greenquo:902966579711578192>"),
            discord.ui.Button(url=url.format(902857046574129172, guild_id), emoji="<:purplequo:902966579812237383>"),
            discord.ui.Button(url=url.format(744990850064580660, guild_id), emoji="<:orangequo:902966579938099200>"),
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


class InvitePrime(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        url = f"https://discord.com/oauth2/authorize?client_id={config.PREMIUM_BOT}&scope=applications.commands%20bot&permissions=21175985838&guild_id={guild_id}"
        self.add_item(discord.ui.Button(url=url, emoji=config.PRIME_EMOJI, label="Invite Prime"))

    @property
    def embed_msg(self):
        return discord.Embed(
            color=config.PREMIUM_COLOR,
            description=(
                "It seems that you don't have the Quotient Prime bot on your server, Also its completely fine if you don't "
                "invite it but We would suggest against it.\n\n*You are paying for the service, why not enjoy it properly?*"
            ),
        )


class GuildSelector(discord.ui.Select):
    def __init__(self, guilds: List[discord.Guild], default=[]):

        _options = []
        for guild in guilds:
            _options.append(
                discord.SelectOption(
                    label=guild.name,
                    value=guild.id,
                    description=f"Owner: {guild.owner} (Members: {guild.member_count})",
                    emoji=emote.diamond if guild.id in default else "<a:right_bullet:898869989648506921>",
                )
            )

        _options.append(
            discord.SelectOption(
                label="Not Listed?", description="Select me if your server is not Listed", value=0, emoji=emote.error
            )
        )
        super().__init__(options=_options, placeholder="Select a server to Upgrade")

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]
