import asyncio
from enum import Enum
from io import BytesIO
from pathlib import Path

import discord
from cogs.esports.views.scrims.utility.selectors import prompt_scrims_slot_selector
from lib.converters import to_async
from models import (
    ErangleLocation,
    MiramarLocation,
    SanhokLocation,
    Scrim,
    ScrimAssignedSlot,
    VikendiLocation,
)
from PIL import Image, ImageDraw, ImageFont

DROP_SELECTOR_LOCK = asyncio.Lock()
REFRESH_TASKS = {}


def get_map_type(map_name: str) -> Enum:
    d = {
        "ERANGLE": ErangleLocation,
        "MIRAMAR": MiramarLocation,
        "SANHOK": SanhokLocation,
        "VIKENDI": VikendiLocation,
    }
    return d[map_name]


class DropLocationSelectorView(discord.ui.View):
    message: discord.Message

    def __init__(self, scrim: Scrim):
        super().__init__(timeout=None)
        self.scrim = scrim
        self.bot = scrim.bot
        self.scrim_map_name: str | None = scrim.game_maps[self.bot.current_time.strftime("%A").upper()]

        if self.scrim_map_name:
            self.map_location: Enum = get_map_type(self.scrim_map_name)

    async def initial_msg(self):
        slots = await self.scrim.assigned_slots.filter(drop_location__isnull=False).order_by("num").prefetch_related("scrim")

        self.clear_items()
        locations = [l.name for l in self.map_location]

        for slot in slots:
            locations.remove(slot.drop_location)

        loca1, loca2 = locations[:25], locations[25:]
        self.add_item(DropLocationSelector(loca1))
        if loca2:
            self.add_item(DropLocationSelector(loca2))

        img = await self.create_image(slots)
        buffer = BytesIO()
        img.save(buffer, "png")
        buffer.seek(0)

        e = discord.Embed(title="Select your drop location...", url=self.bot.config("SUPPORT_SERVER_LINK"), color=self.bot.color)
        e.set_image(url="attachment://map.jpg")

        return e, discord.File(fp=buffer, filename="map.jpg")

    @to_async()
    def create_image(self, slots: list[ScrimAssignedSlot]):
        assets_path = str(Path.cwd() / "quotient" / "assets")
        img_path = str(Path(assets_path) / f"{self.scrim_map_name.lower()}.jpg")
        font_path = str(Path(assets_path) / "font.ttf")

        img = Image.open(img_path)

        font = ImageFont.truetype(font_path, 100)

        draw = ImageDraw.Draw(img)

        for slot in slots:
            draw.text(self.map_location[slot.drop_location].value, str(slot.num), fill="red", font=font)

        return img

    async def refresh_view(self):
        if self.message.id in REFRESH_TASKS:
            REFRESH_TASKS[self.message.id].cancel()

        async def refresh_task():
            await asyncio.sleep(3)
            e, f = await self.initial_msg()
            await self.message.edit(content="", embed=e, attachments=[f], view=self)

        REFRESH_TASKS[self.message.id] = asyncio.create_task(refresh_task())


class DropLocationSelector(discord.ui.Select):
    view: "DropLocationSelectorView"

    def __init__(self, locations: list[str]):

        super().__init__(
            placeholder="Select a drop location ...",
            options=[
                discord.SelectOption(
                    label=location.replace("_", " ").title(),
                    value=location,
                )
                for location in locations
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        slots = await self.view.scrim.assigned_slots.filter(members__contains=interaction.user.id).prefetch_related("scrim")

        if not slots:
            return await interaction.followup.send(
                embed=self.view.bot.error_embed("It seems you don't have any slot in this scrim."),
                ephemeral=True,
            )

        selected_slots = await prompt_scrims_slot_selector(
            interaction, slots, "Select the slot to set the drop location ...", force_dropdown=True
        )

        if not selected_slots:
            return

        selected_slot = selected_slots[0]

        async with DROP_SELECTOR_LOCK:
            if await self.view.scrim.assigned_slots.filter(drop_location=self.values[0]).exists():
                return await interaction.followup.send(
                    embed=self.view.bot.error_embed("This drop location is already taken by someone else.", title="Whoops!"),
                    ephemeral=True,
                )

            selected_slot.drop_location = self.values[0]
            await selected_slot.save(update_fields=["drop_location"])

            await interaction.followup.send(
                embed=self.view.bot.success_embed(
                    f"Successfully claimed drop location `{self.values[0].replace('_', ' ').title()}` for `slot {selected_slot.num}`.\n\n"
                    "`The map image will be updated in a few seconds.`"
                ),
                ephemeral=True,
            )

            await self.view.refresh_view()
