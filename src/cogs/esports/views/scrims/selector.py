from contextlib import suppress
from typing import List, Union

import discord
from core.Context import Context
from core.views import QuotientView

from models import Scrim
from utils import emote

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


# async def scrim_selector(
#     channel: discord.TextChannel,
#     user: Union[discord.Member, discord.User],
#     scrims: List[Scrim],
#     **kwargs,
# ):


#     if len(scrims) <= 25:
#         view = ScrimSelectorView(user, scrims, **kwargs)
#         view.message = await channel.send("Kindly use the dropdown below to select scrims.", view=view)
#         await view.wait()
#         return await Scrim.filter(pk__in=view.custom_id).order_by("id")


async def prompt_selector(ctx: Context, scrims: List[Scrim] = None, *, placeholder: str = None, multi: bool = True):
    placeholder = placeholder or "Choose {0} to continue...".format("Scrims" if multi else "a Scrim")

    scrims = scrims or await Scrim.filter(guild_id=ctx.guild.id).order_by("open_time")
    if not scrims:
        return None

    if len(scrims) == 1:
        return scrims[0]

    view = QuotientView(ctx)

    view.message = await ctx.send(
        "Choose {0} from the dropdown below:".format("Scrims" if multi else "a Scrim"),
        view=view,
    )
    await view.wait()
    if view.custom_id:
        await view.message.delete()

        scrims = view.custom_id.split(",")
        if not len(scrims) > 1:
            return await Scrim.get_or_none(pk=scrims[0])

        return await Scrim.filter(pk__in=scrims)
