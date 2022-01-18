from utils import string_input, truncate_string, QuoMember, BetterFutureTime
from async_property import async_property
from models import Scrim, ReservedSlot
from core import Context
import discord


class SlotReserver(discord.ui.View):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(timeout=60.0)
        self.ctx = ctx
        self.scrim = scrim
        self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "Sorry, you can't use this interaction as it is not started by you.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if hasattr(self, "message"):
            for b in self.children:

                b.style, b.disabled = discord.ButtonStyle.grey, True

            await self.message.edit(embed=await self.updated_embed, view=self)

    @async_property
    async def updated_embed(self):
        reserves = await self.scrim.reserved_slots.all()
        embed = discord.Embed(color=self.ctx.bot.color, title="Reserved-Slots Editor")

        to_show = []
        for i in self.scrim.available_to_reserve:
            check = [j.team_name for j in reserves if j.num == i]

            if check:
                info = check[0]
            else:
                info = "❌"

            to_show.append(f"Slot {i:02}  -->  {info}\n")

        embed.description = f"```{''.join(to_show)}```"
        return embed

    async def refresh_embed(self):
        await self.message.edit(embed=await self.updated_embed, view=self)

    async def ask_embed(self, desc: str, *, image=None):
        embed = discord.Embed(color=self.ctx.bot.color, description=desc, title="Reserved-Slots Editor")
        if image:
            embed.set_image(url=image)
        embed.set_footer(text=f"Reply with 'cancel' to stop this process.")

        return await self.ctx.send(embed=embed)

    async def error_embed(self, desc: str):
        embed = discord.Embed(color=discord.Color.red(), title="Whoopsi-Doopsi", description=desc)
        await self.ctx.send(embed=embed, delete_after=2)

    @discord.ui.button(style=discord.ButtonStyle.success, custom_id="reserve", label="Reserve Slot")
    async def reserve_slot(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        m = await self.ask_embed(
            "Enter the slot details you want to reserve in the following format:\n"
            "> `slot_number`,`team_name`, `team_owner`, `time to reserve`\n\n"
            "Enter `none` in place of:\n"
            "- `team owner` if you want the slot be a management slot.\n"
            "- `time to reserve` if you want the reserve time to never expire.\n\n"
            "**Example to Reserve Management Slot:**\n"
            "`1, Management Slot, none, none` \n*don't forget to separate everything with comma (`,`)*\n",
            image="https://cdn.discordapp.com/attachments/851846932593770496/882492600542720040/reserve_docs.gif",
        )

        slot = await string_input(self.ctx, self.check, delete_after=True)

        await self.ctx.safe_delete(m)
        if slot.strip().lower() == "cancel":
            return await self.error_embed("Alright, Aborting.")

        slot = slot.split(",")
        try:
            num, team_name, team_owner, time_to_reserve = slot
            num = int(num.strip())
            team_name = truncate_string(team_name.strip(), 22)

        except ValueError:
            return await self.error_embed(
                "The details you entered were not according to the proper format. Please try again."
            )

        owner_id = None
        if team_owner.strip().lower() != "none":
            owner = await QuoMember().convert(self.ctx, team_owner.strip())
            owner_id = owner.id

        expire = None
        if time_to_reserve.strip().lower() != "none":
            expire = await BetterFutureTime().convert(self.ctx, time_to_reserve.strip())

        if num not in (_range := self.scrim.available_to_reserve):
            return await self.error_embed(
                f"The slot-number you entered (`{num}`) cannot be reserved.\n"
                f"\nThe slot-number must be a number between `{_range.start}` and `{_range.stop}`"
            )

        to_del = await self.scrim.reserved_slots.filter(num=num).first()
        if to_del:
            await ReservedSlot.filter(pk=to_del.id).delete()

        slot = await ReservedSlot.create(num=num, user_id=owner_id, team_name=team_name, expires=expire)
        await self.scrim.reserved_slots.add(slot)
        if expire and owner_id:
            await self.ctx.bot.reminders.create_timer(
                expire, "scrim_reserve", scrim_id=self.scrim.id, user_id=owner_id, team_name=team_name, num=num
            )

        await self.refresh_embed()

    @discord.ui.button(style=discord.ButtonStyle.red, custom_id="remove", label="Remove Reserved")
    async def remove_reserved(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        m = await self.ask_embed(
            "Which reserved slots do you want to remove?\n"
            "You can enter one or more than one slots, just separate them with a comma (`,`)."
            "\nFor Example:\n`1, 2, 5, 10`"
        )

        slots = await string_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(m)
        if slots.strip().lower() == "cancel":
            return await self.error_embed("Alright, Aborting.")

        slots = slots.split(",")
        try:
            slots = [int(i.strip()) for i in slots]
        except:
            return await self.error_embed("Invalid format provided.")

        slots = await self.scrim.reserved_slots.filter(num__in=slots)
        if not slots:
            return await self.error_embed("Invalid slots provided.")

        await ReservedSlot.filter(id__in=(slot.id for slot in slots)).delete()
        await self.refresh_embed()
