import discord
from lib import TEXT_CHANNEL, keycap_digit
from models import Day, Scrim, ScrimAssignedSlot


class WeekDaysSelector(discord.ui.Select):
    def __init__(self, placeholder="Select the days for registrations", max=7):
        _o = []
        for idx, day in enumerate(Day, start=1):
            _o.append(discord.SelectOption(label=day.name.title(), value=day.value, emoji=keycap_digit(idx)))

        super().__init__(placeholder=placeholder, max_values=max, options=_o)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.stop()

        self.view.selected_days = self.values


class ScrimsSlotSelector(discord.ui.Select):

    def __init__(self, slots: list[ScrimAssignedSlot], multiple: bool = False):

        options = []
        for idx, slot in enumerate(slots[:25], start=1):
            options.append(
                discord.SelectOption(
                    label=f"Slot {slot.num} ─ #{getattr(slot.scrim.registration_channel,'name','deleted-channel')}",
                    description=f"{slot.team_name} (ID: {slot.scrim.id})",
                    value=f"{slot.scrim.id}:{slot.id}",
                    emoji=keycap_digit(idx) if idx <= 9 else "📇",
                )
            )

        super().__init__(placeholder="Select slot(s) from this dropdown...", options=options, max_values=len(slots) if multiple else 1)

    async def callback(self, interaction: discord.Interaction) -> any:
        await interaction.response.edit_message(view=self.view)
        self.view.stop()

        self.view.selected_slots = interaction.data["values"]


class ScrimSelector(discord.ui.Select):
    view: "ScrimSelectorView"

    def __init__(self, placeholder: str, scrims: list[Scrim], max_values: int = 25):
        super().__init__(
            placeholder=placeholder,
            max_values=max_values,
            options=[
                discord.SelectOption(
                    label="#" + getattr(scrim.registration_channel, "name", "Unknown-Channel"),  # type: ignore
                    value=scrim.id,
                )
                for scrim in scrims
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        self.view.selected_scrims = self.values
        self.view.stop()


class ScrimSelectorView(discord.ui.View):
    message: discord.Message
    selected_scrims: list[str] = []

    def __init__(
        self,
        user: discord.Member,
        scrims: list[Scrim],
        placeholder: str = "Select a scrim ...",
        single_scrim_only: bool = False,
    ):
        self.user = user

        super().__init__(timeout=60.0)

        for scrim_group in discord.utils.as_chunks(scrims, 25):
            group = list(scrim_group)

            self.add_item(
                ScrimSelector(
                    placeholder,
                    group,
                    max_values=1 if single_scrim_only else len(group),
                )
            )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(f"Sorry, only **{self.user}** can use this dropdown.", ephemeral=True)
            return False

        return True

    async def on_timeout(self) -> None:
        if hasattr(self, "message"):
            await self.message.delete(delay=0)


async def prompt_scrims_selector(
    send_through: discord.TextChannel | discord.Interaction,
    user: discord.Member,
    scrims: list[Scrim],
    placeholder: str = None,
    single_scrim_only: bool = False,
) -> list[Scrim]:
    placeholder = placeholder or "Choose {0} to continue...".format("a scrim" if single_scrim_only else "scrims")

    if len(scrims) == 1:
        return scrims

    view = ScrimSelectorView(user, scrims, placeholder, single_scrim_only)
    text = "Choose {0} from the dropdown below:".format("a scrim" if single_scrim_only else "scrims")

    if isinstance(send_through, discord.Interaction):
        view.message = await send_through.followup.send(text, view=view, ephemeral=True)

    else:
        view.message = await send_through.send(text, view=view)

    await view.wait()
    if view.selected_scrims:
        await view.message.delete(delay=0)
        return await Scrim.filter(pk__in=view.selected_scrims)
