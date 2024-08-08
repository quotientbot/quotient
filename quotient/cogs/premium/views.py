import os
import re

import discord

from quotient.lib.emojis import PANDA_RUN
from quotient.models import INR_PREMIUM_PLANS, CurrencyType, GuildTier, PremiumTxn, User


def valid_email(email: str):
    return bool(re.search(r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", email))


class UserDetailsForm(discord.ui.Modal):
    def __init__(self, selected_plan: str):
        super().__init__(title="Fill your details")
        self.selected_plan = selected_plan

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        email = str(self.children[0])

        if not valid_email(email):
            return await interaction.followup.send("Invalid email format, please enter a valid email.", ephemeral=True)

        await User.get(pk=interaction.user.id).update(email_id=email)

        tier, price, currency = self.selected_plan.split(":")

        tier = GuildTier[tier]
        price = float(price)

        # Find the corresponding plan
        selected_plan = None
        for plan in INR_PREMIUM_PLANS:
            if plan["tier"] == tier:
                if "price_lifetime" in plan and plan["price_lifetime"] == price:
                    selected_plan = plan
                    duration_key = "lifetime"
                    break
                elif "price_per_month" in plan and plan["price_per_month"] == price:
                    selected_plan = plan
                    duration_key = "month"
                    break
                elif "price_per_year" in plan and plan["price_per_year"] == price:
                    selected_plan = plan
                    duration_key = "year"
                    break

        duration = selected_plan["durations"][duration_key]

        txn = await PremiumTxn.create(
            user_id=interaction.user.id,
            guild_id=interaction.guild.id,
            amount=price,
            currency=CurrencyType[currency],
            tier=tier,
            premium_duration=duration,
        )

        if txn.bot.is_main_instance is False:
            await txn.copy_to_main()

        _link = os.getenv("PAYMENT_SERVER_LINK") + "/payment?txnId=" + str(txn.txnid)

        v = discord.ui.View()
        v.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="Complete Payment",
                url=_link,
            )
        )

        await interaction.followup.send(
            f"## You are about to purchase Quotient Pro for **__{interaction.guild.name}__**.\n"
            "If you want to purchase for another server, use `/premium` command in that server.",
            view=v,
            ephemeral=True,
        )


class PlanSelector(discord.ui.Select):
    view: "RequirePremiumView"

    def __init__(self, placeholder: str):
        super().__init__(placeholder=placeholder)

        for inr_plan in INR_PREMIUM_PLANS:
            description = inr_plan.get("description", "No description available.")

            if inr_plan.get("price_lifetime", None):
                self.add_option(
                    label=f"{inr_plan['tier'].name} - ₹{inr_plan['price_lifetime']} / Lifetime",
                    value=f"{inr_plan['tier'].name}:{inr_plan['price_lifetime']}:INR",
                    emoji=inr_plan["emote"],
                    description=description,
                )
                continue

            self.add_option(
                label=f"{inr_plan['tier'].name} - ₹{inr_plan['price_per_month']} / Month",
                value=f"{inr_plan['tier'].name}:{inr_plan['price_per_month']}:INR",
                emoji=inr_plan["emote"],
                description=description,
            )

            self.add_option(
                label=f"{inr_plan['tier'].name} - ₹{inr_plan['price_per_year']} / Year",
                value=f"{inr_plan['tier'].name}:{inr_plan['price_per_year']}:INR",
                emoji=inr_plan["emote"],
                description=description,
            )

    async def callback(self, interaction: discord.Interaction):
        u = await User.get(pk=interaction.user.id)
        modal = UserDetailsForm(interaction.data["values"][0])
        modal.add_item(
            discord.ui.TextInput(
                label="Email ID",
                placeholder="(Used to send payment receipt only)",
                default=u.email_id,
                min_length=8,
                max_length=50,
            )
        )

        await interaction.response.send_modal(modal)


class RequirePremiumView(discord.ui.View):
    def __init__(self, text: str, placeholder="Select a Quotient Pro Plan... "):
        super().__init__(timeout=None)
        self.text = text
        self.add_item(PlanSelector(placeholder=placeholder))

    @property
    def premium_embed(self) -> discord.Embed:
        e = discord.Embed(
            color=int(os.getenv("DEFAULT_COLOR")),
        )
        e.description = self.text

        e.set_image(url="https://cdn.discordapp.com/attachments/782161513825042462/1269440209452269699/image.png")
        return e


async def prompt_premium_plan(
    inter: discord.Interaction, text: str = None, min_tier: GuildTier = None, placeholder="Select a Quotient Pro Plan... "
) -> None:
    if text is None:
        text = (
            f"Your server needs to be on **{min_tier.name}** tier to use this feature, Consider upgrading to a Quotient Pro Plan now!"
        )

    v = RequirePremiumView(text, placeholder)
    await inter.followup.send(embed=v.premium_embed, view=v, ephemeral=True)


class UpgradeButton(discord.ui.Button):
    def __init__(self, label: str = "Upgrade Server"):
        super().__init__(label=label, style=discord.ButtonStyle.blurple, emoji=PANDA_RUN)

    async def callback(self, interaction: discord.Interaction):
        v = RequirePremiumView(text="")
        await interaction.response.send_message(embed=v.premium_embed, view=v, ephemeral=True)
