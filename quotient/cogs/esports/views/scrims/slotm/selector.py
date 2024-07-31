import discord
from lib import keycap_digit

from quotient.models.esports import ScrimsSlotManager


class ScrimSlotmSelector(discord.ui.Select):
    def __init__(self, records: list[ScrimsSlotManager], placeholder: str):
        options = []
        for idx, record in enumerate(records, start=1):
            options.append(
                discord.SelectOption(
                    label=f"#{record.bot.get_channel(record.channel_id)}",
                    value=record.id,
                    emoji=keycap_digit(idx) if idx <= 9 else "📇",
                )
            )

        super().__init__(
            placeholder=placeholder,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> any:
        await interaction.response.edit_message(view=self.view)
        self.view.selected_slotm = interaction.data["values"][0]
        self.view.stop()


async def prompt_slotm_selector(
    inter: discord.Interaction, msg: str, placeholder: str = "Select the slotm panel..."
) -> ScrimsSlotManager:

    records = await ScrimsSlotManager.filter(guild_id=inter.guild_id)
    if not records:
        return None

    if len(records) == 1:
        return records[0]

    view = discord.ui.View(timeout=100)
    view.add_item(ScrimSlotmSelector(records, placeholder))

    m = await inter.followup.send(msg, view=view, ephemeral=True)

    await view.wait()
    await m.delete(delay=0)

    if not view.selected_slotm:
        return None

    return await ScrimsSlotManager.get_or_none(id=view.selected_slotm)
