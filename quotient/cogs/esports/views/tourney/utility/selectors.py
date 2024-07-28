import discord
from models import Tourney


class TourneySelector(discord.ui.Select):
    view: "TourneySelectorView"

    def __init__(self, placeholder: str, tourneys: list[Tourney], max_values: int = 25):
        super().__init__(
            placeholder=placeholder,
            max_values=max_values,
            options=[
                discord.SelectOption(
                    label="#" + getattr(tourney.registration_channel, "name", "Unknown-Channel"),  # type: ignore
                    value=tourney.id,
                )
                for tourney in tourneys
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        self.view.selected_tourneys = self.values
        self.view.stop()


class TourneySelectorView(discord.ui.View):
    message: discord.Message
    selected_tourneys: list[str] = []

    def __init__(
        self,
        user: discord.Member,
        tourneys: list[Tourney],
        placeholder: str = "Select a tourney ...",
        single_tourney_only: bool = False,
    ):
        self.user = user

        super().__init__(timeout=60.0)

        for tourney_group in discord.utils.as_chunks(tourneys, 25):
            group = list(tourney_group)

            self.add_item(
                TourneySelector(
                    placeholder,
                    group,
                    max_values=1 if single_tourney_only else len(group),
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


async def prompt_tourneys_selector(
    inter: discord.Interaction,
    tourneys: list[Tourney],
    placeholder: str = None,
    single_tourney_only: bool = True,
    force_dropdown: bool = False,
) -> list[Tourney]:
    placeholder = placeholder or "Choose {0} to continue...".format("a tourney" if single_tourney_only else "tourneys")

    if len(tourneys) == 1 and not force_dropdown:
        return tourneys

    view = TourneySelectorView(inter.user, tourneys, placeholder, single_tourney_only)
    text = "Choose {0} from the dropdown below:".format("a tourney" if single_tourney_only else "tourneys")

    view.message = await inter.followup.send(text, view=view, ephemeral=True)

    await view.wait()
    if view.selected_tourneys:
        await view.message.delete(delay=0)
        return await Tourney.filter(pk__in=view.selected_tourneys)
