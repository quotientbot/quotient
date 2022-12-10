from typing import List

import config
import discord
from utils import emote
from models import PremiumPlan, PremiumTxn


class PlanSelector(discord.ui.Select):
    def __init__(self, plans: List[PremiumPlan]):
        super().__init__(placeholder="Select a Quotient Premium Plan... ")

        for _ in plans:
            self.add_option(label=f"{_.name} - ₹{_.price}", description=_.description, value=_.id)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.plan = self.values[0]
        self.view.stop()


class PremiumPurchaseBtn(discord.ui.Button):
    def __init__(self, label="Get Quotient Pro", emoji=emote.diamond, style=discord.ButtonStyle.grey):
        super().__init__(style=style, label=label, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        v = discord.ui.View(timeout=100)
        v.plan: str = None

        v.add_item(PlanSelector(await PremiumPlan.all().order_by("id")))
        await interaction.followup.send("Please select the Quotient Pro plan, you want to opt:", view=v, ephemeral=True)
        await v.wait()

        if not v.plan:
            return

        txn = await PremiumTxn.create(
            txnid=await PremiumTxn.gen_txnid(),
            user_id=interaction.user.id,
            guild_id=interaction.guild.id,
            plan_id=v.plan,
        )
        _link = config.PAY_LINK + "getpremium" + "?txnId=" + txn.txnid

        await interaction.followup.send(
            f"You are about to purchase Quotient Premium for **{interaction.guild.name}**.\n"
            "If you want to purchase for another server, use `qpremium` or `\premium` command in that server.\n\n"
            f"[*Click Me to Complete the Payment*]({_link})",
            ephemeral=True,
        )


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

        _e.description += f"\n`{self.text}`"
        _e.set_image(url="https://cdn.discordapp.com/attachments/851846932593770496/991209774123339816/premium_plans.gif")
        return _e


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
        await interaction.response.defer()
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]
