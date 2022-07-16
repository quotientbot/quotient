from contextlib import suppress
from typing import List, Union

import discord
from aiocache import cached

from core.Context import Context
from core.views import QuotientView
from models import Scrim
from utils import emote, split_list

__all__ = ("ScrimSelectorView",)


class ScrimSelector(discord.ui.Select):
    view: "ScrimSelectorView"

    def __init__(self, placeholder: str, scrims: List[Scrim], max_values=25):

        _options = []
        for scrim in scrims:
            _options.append(
                discord.SelectOption(
                    label=scrim.registration_channel.name,  # type: ignore
                    value=scrim.id,
                    description=f"{scrim.name} (ScrimID: {scrim.id})",
                    emoji=emote.TextChannel,
                )
            )

        # print(scrims, _options)
        super().__init__(placeholder=placeholder, options=_options, max_values=max_values)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.custom_id = self.values

        self.view.stop()


class ScrimSelectorView(discord.ui.View):
    message: discord.Message
    custom_id: List[str] = []

    def __init__(self, user: Union[discord.Member, discord.User], scrims: List[Scrim], **kwargs):
        self.user = user

        timeout = kwargs.get("timeout", 30)
        placeholder = kwargs.get("placeholder", "Select a scrim ...")
        max_values = kwargs.get("max_values", len(scrims))

        super().__init__(timeout=timeout)

        # scrims = scrims[:25]

        self.add_item(ScrimSelector(placeholder, scrims, max_values))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(f"Sorry, only **{self.user}** can use this dropdown.", ephemeral=True)
            return False

        return True

    async def on_timeout(self) -> None:
        if hasattr(self, "message"):
            with suppress(discord.HTTPException):
                await self.message.delete()


async def prompt_selector(ctx: Context, scrims: List[Scrim] = None, *, placeholder: str = None, multi: bool = True):
    placeholder = placeholder or "Choose {0} to continue...".format("Scrims" if multi else "a Scrim")

    scrims = scrims or await Scrim.filter(guild_id=ctx.guild.id).order_by("open_time")
    if not scrims:
        return None

    if len(scrims) == 1:
        return scrims[0]

    view = QuotientView(ctx)
    if len(scrims) <= 25:
        view.add_item(Select(placeholder, scrims, multi=multi))
    else:
        for scrims_chunk in split_list(scrims, 25):
            view.add_item(Select(placeholder, scrims_chunk, multi=multi))

    view.message = await ctx.send(
        "Choose {0} from the dropdown below:".format("Scrims" if multi else "a Scrim"),
        view=view,
    )
    await view.wait()
    if view.custom_id:
        await view.message.delete()

        if not len(view.custom_id) > 1:
            return await Scrim.get_or_none(pk=view.custom_id[0])

        return await Scrim.filter(pk__in=view.custom_id)


class Select(discord.ui.Select):
    view: QuotientView

    def __init__(self, placeholder: str, scrims: List[Scrim], multi: bool):
        _options = []
        for scrim in scrims:
            _options.append(
                discord.SelectOption(
                    label=getattr(scrim.registration_channel, "name", "deleted-channel"),  # type: ignore
                    value=scrim.id,
                    description=f"{scrim.name} (ScrimID: {scrim.id})",
                    emoji=emote.TextChannel,
                )
            )

        super().__init__(placeholder=placeholder, options=_options, max_values=len(_options) if multi else 1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.custom_id = self.values

        self.view.stop()


@cached(ttl=10)
async def scrim_position(scrim_id: int, guild_id: int):
    """
    returns the position of scrim in all scrims of a server
    """
    scrims = await Scrim.filter(guild_id=guild_id).order_by("open_time")
    return str(scrims.index(next(s for s in scrims if s.pk == scrim_id)) + 1), len(scrims).__str__()
