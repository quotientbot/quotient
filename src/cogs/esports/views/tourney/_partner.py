import discord

from core import Context
from models import MediaPartner, Tourney
from utils import aenumerate, channel_input, integer_input

from ..base import EsportsBaseView


class MediaPartnerView(EsportsBaseView):
    def __init__(self, ctx: Context, *, tourney: Tourney):
        super().__init__(ctx, timeout=30, title="Tourney Media Partner")
        self.tourney = tourney
        self.ctx = ctx

    async def initial_embed(self):
        embed = discord.Embed(title="Tournament Media Partnership", url=self.ctx.config.SERVER_LINK)
        embed.color = self.bot.color
        embed.description = (
            "With media-partnership you can make Quotient handle media partner registrations "
            "that means in Quotient will check if the user have registered in the partner server "
            "and if they have, their registration will be accepted and slot will be given to them.\n\n"
        )

        async for idx, partner in aenumerate(self.tourney.media_partners.all(), start=1):
            embed.description += f"`{idx:02}.` {getattr(partner.channel,'mention','deleted-channel')} - **{await partner.slots.all().count()} players**\n"

        embed.description += "\n`Click Add New to create a new media partner.`"
        return embed

    async def __refresh_embed(self):
        await self.tourney.refresh_from_db()
        try:
            self.message = await self.message.edit(embed=await self.initial_embed(), view=self)
        except discord.HTTPException:
            await self.on_timeout()

    @discord.ui.button(label="Add New", style=discord.ButtonStyle.green)
    async def add_partner(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)

        if await self.tourney.media_partners.all().count() >= 1 and not await self.ctx.is_premium_guild():
            return await self.ctx.error(
                "You need Quotient Premium to download Ms Excel file containing all the "
                f"registration data of your tourneys.\n\n"
                "Buy Premium for just ₹29 here: https://quotientbot.xyz/premium",
                6,
            )

        m = await self.ask_embed("Enter the tourney ID of the tournament you want to partner with.")

        tourney_id = await integer_input(self.ctx, self.check, delete_after=True)

        await self.ctx.safe_delete(m)

        tourney = await Tourney.get_or_none(pk=tourney_id)
        if tourney is None or not (guild := tourney.guild):
            return await self.error_embed(
                "The tourney ID you entered is invalid. \n\nKindly use `qt` in the partner server"
                "to get the correct ID."
            )

        if guild == self.ctx.guild:
            return await self.error_embed("You can't partner with a tournament running in your server.")

        if tourney_id in (p.tourney_id for p in await self.tourney.media_partners.all()):
            return await self.error_embed(f"The tourney you entered is already partnered with {tourney}.")

        if not guild.chunked:
            self.bot.loop.create_task(guild.chunk())

        if not await self.bot.get_or_fetch_member(guild, self.ctx.author.id):
            return await self.error_embed(
                "You are not even in the server you are trying to media partner with.\n\n"
                "Kindly join the server first or gimme right ID."
            )

        m = await self.ask_embed(
            "Which channel do you want to use for Media-Partner?\n\n" "`Mention the channel or enter its ID.`"
        )
        channel = await channel_input(self.ctx, self.check, delete_after=True)

        await self.ctx.safe_delete(m)

        channel_check = await MediaPartner.get(channel_id=channel.id).exists()
        if channel_check:
            return await self.error_embed(f"{channel.mention} is already a media partner channel")

        tourney_check = await MediaPartner.get(tourney_id=tourney_id).exists()
        if tourney_check:
            return await self.error_embed(f"{str(tourney)} is already media-partnered in other channel.")

        partner = await MediaPartner.create(tourney_id=tourney.id, channel_id=channel.id)
        await self.tourney.media_partners.add(partner)
        self.bot.cache.media_partner_channels.add(channel.id)
        await self.__refresh_embed()

    @discord.ui.button(style=discord.ButtonStyle.red, label="Remove")
    async def remove_partner(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)

        m = await self.ask_embed(
            "Which channel do you want to remove from media partner?\n\n"
            "`Note that this will not impact slots in anyway.`"
        )

        _channel = await channel_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(m)

        if not await self.tourney.media_partners.filter(pk=_channel.id).exists():
            return await self.error_embed("This is not a media-partner channel of {0}".format(self.tourney))

        self.bot.cache.media_partner_channels.discard(_channel.id)
        await MediaPartner.filter(pk=_channel.id).delete()
        await self.ctx.success(f"Removed {_channel.mention} from Media-Partner Channels.", 4)
        await self.__refresh_embed()
