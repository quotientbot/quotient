import os
import re

import discord
from lib import emojis
from models import PremiumPlan, PremiumTxn, User

from .consts import get_pro_features_formatted


class PlanSelector(discord.ui.Select):
    def __init__(self, plans: list[PremiumPlan]):
        super().__init__(placeholder="Select a Quotient Pro Plan... ")

        for _ in plans:
            self.add_option(
                label=f"{_.name} - ₹{_.price}", description=_.description, value=_.id
            )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.selected_plan = self.values[0]
        self.view.stop()


def valid_email(email: str):
    return bool(re.search(r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", email))


class UserDetailsForm(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Fill your details")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        email, phone = str(self.children[0]), str(self.children[1])

        if not valid_email(email):
            return await interaction.followup.send(
                "Invalid email format, please enter a valid email.", ephemeral=True
            )

        if not phone.isdigit() or len(phone) < 10:
            return await interaction.followup.send(
                "Invalid phone number format, please enter a valid phone number.",
                ephemeral=True,
            )

        await User.get(pk=interaction.user.id).update(
            email_id=email, phone_number=phone
        )

        v = discord.ui.View(timeout=100)
        v.selected_plan = None

        v.add_item(PlanSelector(await PremiumPlan.all().order_by("id")))
        await interaction.followup.send(
            "Please select the Quotient Pro plan, you want to opt:",
            view=v,
            ephemeral=True,
        )
        await v.wait()

        if not v.selected_plan:
            return

        txn = await PremiumTxn.create(
            txnid=await PremiumTxn.generate_txnid(),
            user_id=interaction.user.id,
            guild_id=interaction.guild.id,
            plan_id=v.selected_plan,
        )

        _link = os.getenv("PAYMENT_SERVER_LINK") + "?txnId=" + txn.txnid

        v = discord.ui.View()
        v.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="Complete Payment",
                url=_link,
            )
        )

        await interaction.followup.send(
            f"## You are about to purchase Quotient Premium for **__{interaction.guild.name}__**.\n"
            "If you want to purchase for another server, use `/premium` command in that server.",
            view=v,
            ephemeral=True,
        )


class PremiumPurchaseBtn(discord.ui.Button):
    def __init__(
        self,
        label="Get Quotient Pro",
        emoji=emojis.DIAMOND,
        style=discord.ButtonStyle.grey,
    ):
        super().__init__(style=style, label=label, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        user = await User.get(pk=interaction.user.id)
        form = UserDetailsForm()

        form.add_item(
            discord.ui.TextInput(
                label="Email",
                placeholder="Used to send payment receipt...",
                default=user.email_id or "",
                min_length=5,
                max_length=50,
            )
        )
        form.add_item(
            discord.ui.TextInput(
                label="Phone Number",
                placeholder="Used to send payment receipt...",
                default=user.phone_number or "",
                min_length=10,
                max_length=10,
            )
        )

        await interaction.response.send_modal(form)


class PremiumView(discord.ui.View):
    def __init__(
        self,
        text="This feature requires Quotient Pro.",
        *,
        label="Get Quotient Pro",
    ):
        super().__init__(timeout=None)
        self.text = text
        self.add_item(PremiumPurchaseBtn(label=label))

    @property
    def premium_embed(self) -> discord.Embed:
        _e = discord.Embed(
            color=0x00FFB3,
            description=f"**You discovered a premium feature <a:premium:807911675981201459>**",
        )
        _e.description = f"\n*`{self.text}`*\n\n__Perks you get with Quotient Pro:__\n"
        _e.description += get_pro_features_formatted()
        return _e
