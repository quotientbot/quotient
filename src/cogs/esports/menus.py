from __future__ import annotations

import string

import aiohttp
from discord.ext import menus
from discord.ext.menus import Button

import config
import constants
from models import Scrim
from models.helpers import *  # noqa: F401, F403
from utils import *  # noqa: F401, F403

from .errors import ScrimError
from .helpers import delete_denied_message, scrim_work_role

# class PointsConfigEditor(menus.Menu):
#     def __init__(self, points: PointsInfo):
#         super().__init__(
#             timeout=60,
#             delete_message_after=False,
#             clear_reactions_after=True,
#         )

#         self.points = points
#         self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

#     def inital_embed(self):
#         points = self.points
#         embed = discord.Embed(color=self.bot.color, title=f"Ptable Setup Editor: {points.id}")

#         fields = {
#             "Title": points.title,
#             "Secondary Title": points.secondary_title,
#             "Watermark": points.footer,
#             "Channel": getattr(points.channel, "mention", "`Not Found!`"),
#             "Per kill point": points.kill_points,
#             "Default Position Points": "Click me for preview",
#         }

#         for idx, (name, value) in enumerate(fields.items()):
#             embed.add_field(
#                 name=f"{regional_indicator(string.ascii_uppercase[idx])} {name}:",
#                 value=value,
#                 inline=False,
#             )

#         embed.set_thumbnail(url=self.bot.user.display_avatar.url)
#         return embed

#     async def send_initial_message(self, ctx, channel):
#         return await channel.send(embed=self.inital_embed())

#     async def refresh(self):
#         self.points = await PointsInfo.get(id=self.points.id)
#         await self.message.edit(embed=self.inital_embed())

#     @menus.button(regional_indicator("A"))
#     async def on_a(self, payload):
#         msg = await self.ctx.simple(
#             f"What do you want the title of points table to be?\n\n`Please enter a title under 22 characters.`"
#         )

#         title = await inputs.string_input(self.ctx, self.check, delete_after=True)
#         await inputs.safe_delete(msg)

#         if len(title) > 22:
#             return await self.ctx.error("Character length of title cannot exceed 22 characters.", delete_after=3)

#         await PointsInfo.filter(id=self.points.id).update(title=title)
#         await self.refresh()

#     @menus.button(regional_indicator("B"))
#     async def on_b(self, payload):
#         msg = await self.ctx.simple(
#             "What do you want to secondary title to be? This will be shown under the main title.\n\n`Please keep this under 22 characters.`"
#         )

#         title = await inputs.string_input(self.ctx, self.check, delete_after=True)
#         await inputs.safe_delete(msg)

#         if len(title) > 22:
#             return await self.ctx.error(
#                 "Character length of secondary title cannot exceed 22 characters.", delete_after=3
#             )

#         await PointsInfo.filter(id=self.points.id).update(secondary_title=title)
#         await self.refresh()

#     @menus.button(regional_indicator("C"))
#     async def on_c(self, payload):
#         if not await self.ctx.is_premium_guild():
#             return await self.ctx.error(
#                 "This feature is available to premium servers only.\n\nYou can upgrade your server with Quotient Premium to use this.\n\n`Kindly use qperks cmd to know more.`",
#                 delete_after=4,
#             )

#         msg = await self.ctx.simple("What do you want the footer text to be?\n\n`Please keep it under 50 characters.`")
#         title = await inputs.string_input(self.ctx, self.check, delete_after=True)
#         await inputs.safe_delete(msg)

#         if len(title) > 50:
#             return await self.ctx.error("Character length of footer cannot exceed 50 characters.", delete_after=3)

#         await PointsInfo.filter(id=self.points.id).update(footer=title)
#         await self.refresh()

#     @menus.button(regional_indicator("D"))
#     async def on_d(self, payload):
#         msg = await self.ctx.simple(
#             f"Which channel should I use to send points tables?\n\n`Either mention the channel or write its name`"
#         )

#         channel = await inputs.channel_input(self.ctx, self.check, delete_after=True)
#         await inputs.safe_delete(msg)

#         perms = channel.permissions_for(self.ctx.me)
#         if not all((perms.send_messages, perms.embed_links)):
#             return await self.ctx.error(
#                 f"kindly make sure I have `send_messages` and `embed_links` permissions in {channel.mention}",
#                 delete_after=3,
#             )

#         await PointsInfo.filter(id=self.points.id).update(channel_id=channel.id)
#         await self.refresh()

#     @menus.button(regional_indicator("E"))
#     async def on_e(self, payload):
#         msg = await self.ctx.simple(
#             f"How many points do you want me to give per kill?\n\n`Enter a number between 1 and 10.`"
#         )
#         kill_point = await inputs.integer_input(self.ctx, self.check, delete_after=True, limits=(0, 10))
#         await inputs.safe_delete(msg)
#         await PointsInfo.filter(id=self.points.id).update(kill_points=kill_point)
#         await self.refresh()

#     @menus.button(regional_indicator("F"))
#     async def on_f(self, payload):
#         return await self.ctx.error(
#             f"This feature is currently under development, it will be available soon", delete_after=3
#         )

#     @menus.button("\N{BLACK SQUARE FOR STOP}")
#     async def on_stop(self, payload):
#         self.stop()


# class PointsMenu(menus.Menu):
#     def __init__(self, points: PointsInfo, msg: discord.Message):
#         super().__init__(
#             timeout=60,
#             delete_message_after=False,
#             clear_reactions_after=True,
#         )
#         self.msg = msg
#         self.points = points
#         self._dict = {}
#         self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

#     def table_embed(self):
#         table = PrettyTable()
#         table.field_names = ["S.No", "Team Name", "Posi Pt", "Kills", "Total"]
#         for idx, teams in enumerate(self._dict.items(), start=1):
#             team = teams[0]
#             _list = teams[1]
#             win, posi, kill, total = _list
#             table.add_row([idx, textwrap.fill(team, width=12), posi, kill, total])

#         embed = discord.Embed(color=self.bot.color, title=self.points.title)
#         embed.description = f"```ml\n{table.get_string()}```"
#         return embed

#     def initial_embed(self):
#         embed = discord.Embed(color=self.bot.color)
#         embed.description = "▶️ | Start or Edit points table\n" "❌ | Do not save & abort\n" "✅ | Save and Create Image"
#         return embed

#     async def send_initial_message(self, ctx, channel):
#         await self.msg.edit(embed=self.table_embed())
#         return await channel.send(embed=self.initial_embed())

#     async def pointsembed(self, description: str):
#         embed = discord.Embed(color=self.bot.color, title=f"📊 Points Table Menu")
#         embed.description = description
#         return await self.ctx.send(embed=embed, embed_perms=True)

#     async def refresh(self):
#         try:
#             await self.msg.edit(embed=self.table_embed())
#         except Exception as e:
#             await self.ctx.send(e)

#     @menus.button("▶️")
#     async def on_start(self, payload):
#         msg = await self.pointsembed(
#             "Enter team names with their kill points.\n"
#             "Format:\n`<Team Name> = <Kills>`\nKindly don't use special characters in team names.\n"
#             "Separate them with comma (`,`)\n"
#             "Example:\n"
#             "```Team Quotient = 20,\nTeam Butterfly = 14,\nTeam Kite = 5,\nTeam 4Pandas = 8```\n"
#             "Write these according to their position in match.\n"
#             "You have 10 minutes to answer this."
#         )
#         teams = await inputs.string_input(self.ctx, self.check, delete_after=True, timeout=600)
#         await inputs.safe_delete(msg)

#         result = {}
#         try:

#             for idx, line in enumerate(teams.replace("\n", "").split(","), start=1):
#                 line_values = [value.strip() for value in line.split("=")]

#                 teamname = " ".join(
#                     normalize("NFKC", line_values[0]).lower().replace("team", "").replace("name", "").split()
#                 )
#                 # teamname = (
#                 #     re.sub(r"<@*#*!*&*\d+>|team|name|[^\w\s]", "", normalize("NFKC", line_values[0].lower()))
#                 # ).split()[0]

#                 posi = self.points.posi_points.get(str(idx), 0)
#                 kills = int(line_values[1]) * self.points.kill_points

#                 if kills > 99:
#                     return await self.ctx.error(
#                         f"Kills value (`{kills}`) too large at **{str(line_values[0])}**", delete_after=4
#                     )

#                 if not teamname:
#                     return await self.ctx.error(f"I couldn't determine team name.", delete_after=4)

#                 if len(teamname) > 22:
#                     return await self.ctx.error(f"Team name too large at **{teamname}**", delete_after=4)

#                 result[teamname] = [1 if idx == 1 else 0, posi, kills, posi + kills]

#         except Exception as e:
#             return await self.ctx.error(f"Oops , you entered wrong format", delete_after=3)

#         if len(result) > 25:
#             return await self.ctx.error(f"You cannot enter more than 25 teams :c", delete_after=4)

#         _dict = dict(sorted(result.items(), key=lambda x: x[1][3], reverse=True))
#         self._dict.update(_dict)
#         await self.refresh()

#     @menus.button("❌")
#     async def on_cross(self, payload):
#         self.stop()

#     @menus.button("✅")
#     async def on_check(self, payload):
#         table = await PointsTable.create(
#             points_table=str(self._dict),
#             created_by=self.ctx.author.id,
#             created_at=(datetime.now(constants.IST).replace(hour=0, minute=0, second=0, microsecond=0)),
#         )
#         await self.points.data.add(table)
#         await self.ctx.success(
#             f"Successfully created points table.\n\nYou can use `pt match show {self.points.id}` to get it in image format.\nOr you can send the image to a channel with `pt match send {self.points.id}`"
#         )
#         self.stop()


class IDPMenu(menus.Menu):
    def __init__(self, send_channel: QuoTextChannel, role: QuoRole):
        super().__init__(timeout=60, delete_message_after=False, clear_reactions_after=True)
        self.embed = None
        self._id = "Not Set!"
        self._pass = "Not Set!"
        self.msg = None
        self.send_channel = send_channel
        self.ping_role = role
        self.delete_in = 30
        self.id_pass_content = False
        self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

    def idp_embed(self):
        embed = self.ctx.bot.embed(self.ctx, title="New Custom Room. JOIN NOW!")
        embed.set_thumbnail(url=self.ctx.guild.icon.url)
        embed.add_field(name="Room ID", value=self._id)
        embed.add_field(name="Password", value=self._pass)
        embed.add_field(name="Map", value="Not Set")
        embed.add_field(name="Match Starts at", value="Not Set")

        embed.set_footer(
            text=f"Shared by: {self.ctx.author} • Auto delete in {plural(self.delete_in):minute|minutes}.",
            icon_url=self.ctx.author.display_avatar.url,
        )
        return embed

    @staticmethod
    def inital_embed():
        embed = discord.Embed(color=config.COLOR, title="ID-PASS Menu")
        embed.description = (
            "🇹 | Set Title\n"
            "🆔 | Set Room ID\n"
            "🇵 | Set Room Password\n"
            "🗺️ | Set Room Map\n"
            "🕰️ | Set Start Time\n"
            "🖼️ | Set thumbnail image\n"
            "❔ | ID/Pass as Content\n"
            "⏰ | Autodelete after\n"
        )
        return embed

    async def refresh(self):
        try:
            content = self.ping_role.mention if self.ping_role else ""
            if self.id_pass_content:
                content += f"\nID: {self._id} | Password: {self._pass}"
            await self.msg.edit(
                content=content,
                embed=self.embed,
                allowed_mentions=discord.AllowedMentions(everyone=False, roles=False),
            )
        except:
            self.stop()

    async def cembed(self, description):
        return await self.ctx.send(
            embed=discord.Embed(
                color=discord.Color(config.COLOR),
                title=f"🛠️ ID/Pass Formatter",
                description=description,
            )
        )

    async def send_initial_message(self, ctx, channel):
        self.embed = self.idp_embed()
        self.msg = await channel.send(embed=self.idp_embed())
        return await channel.send(embed=self.inital_embed())

    @menus.button(regional_indicator("T"))
    async def set_title(self, payload):
        msg = await self.cembed(
            f"What do you want the title to be?\n\nTitle cannot exceed 256 characters."
        )

        title = await inputs.string_input(self.ctx, self.check, delete_after=True)
        if len(title) > 256:
            return await self.ctx.error(f"Title cannot exceed 256 characters.", delete_after=3)

        await inputs.safe_delete(msg)
        if title.lower() == "none":
            self.embed.title = None
        else:
            self.embed.title = title
        await self.refresh()

    @menus.button("🆔")
    async def set_id(self, payload):
        msg = await self.cembed(f"What is the ID of custom room?")

        _id = await inputs.string_input(self.ctx, self.check, delete_after=True)

        await inputs.safe_delete(msg)
        self.embed.set_field_at(0, name="Room ID", value=_id)
        self._id = _id
        await self.refresh()

    @menus.button("🇵")
    async def set_pass(self, payload):
        msg = await self.cembed(f"What is the password for room?")

        _pass = await inputs.string_input(self.ctx, self.check, delete_after=True)

        await inputs.safe_delete(msg)
        self.embed.set_field_at(1, name="Password", value=_pass)
        self._pass = _pass
        await self.refresh()

    @menus.button("🗺️")
    async def set_map(self, payload):
        msg = await self.cembed(f"What is the name of map?")

        _map = await inputs.string_input(self.ctx, self.check, delete_after=True)

        await inputs.safe_delete(msg)
        self.embed.set_field_at(2, name="Maps", value=_map)
        await self.refresh()

    @menus.button("🕰️")
    async def set_starttime(self, payload):
        msg = await self.cembed(f"What is the match start time?")

        start_time = await inputs.string_input(self.ctx, self.check, delete_after=True)

        await inputs.safe_delete(msg)
        self.embed.set_field_at(3, name="Match Starts at", value=start_time)
        await self.refresh()

    @menus.button("🖼️")
    async def set_thumbnail(self, payload):
        msg = await self.cembed(f"Enter the Image URL you want to set as thumbnail.")
        image = await inputs.string_input(self.ctx, self.check, delete_after=True)

        await inputs.safe_delete(msg)

        if image.lower() == "none":
            self.embed.set_thumbnail(url=None)
        else:
            try:
                image_formats = ("image/png", "image/jpeg", "image/jpg", "image/gif")
                res = await self.bot.session.get(image)
                if res.headers["content-type"] in image_formats:
                    check = True

                else:
                    check = False

            except aiohttp.client_exceptions.InvalidURL:
                return await self.ctx.error(f"This is not a valid Image URL", delete_after=3)

            if not check:
                return await self.ctx.error(
                    f"The URL didn't contain a valid Image format.", delete_after=3
                )

            self.embed.set_thumbnail(url=image)
            await self.refresh()

    @menus.button("❔")
    async def idp_content(self, payload):
        self.id_pass_content = not self.id_pass_content
        await self.refresh()

    @menus.button("⏰")
    async def delete_time(self, payload):
        msg = await self.cembed(
            f"After how many minutes do you want me to delete the idp message?\nIt can be between 1-30"
        )
        delete_time = await inputs.integer_input(
            self.ctx, self.check, delete_after=True, limits=(None, None)
        )
        await inputs.safe_delete(msg)
        self.delete_in = delete_time
        self.embed.set_footer(
            text=f"Shared by: {self.ctx.author} • Auto delete in {plural(self.delete_in):minute|minutes}",
            icon_url=self.ctx.author.display_avatar.url,
        )
        await self.refresh()

    @menus.button("❌")
    async def on_cancel(self, payload):
        self.stop()

    @menus.button("✅")
    async def on_confirm(self, payload):
        content = self.ping_role.mention if self.ping_role else ""
        if self.id_pass_content:
            content += f"\nID: {self._id} | Password: {self._pass}"

        msg = await self.send_channel.send(
            content=content,
            embed=self.embed,
            allowed_mentions=discord.AllowedMentions(everyone=True, roles=True),
        )

        self.bot.loop.create_task(delete_denied_message(msg, self.delete_in * 60))
        self.stop()


class AutocleanMenu(menus.Menu):
    def __init__(self, *, scrim: Scrim):
        super().__init__(
            timeout=60,
            delete_message_after=False,
            clear_reactions_after=True,
        )
        self.scrim = scrim
        self.days = scrim.open_days
        self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

    def initial_embed(self):
        scrim = self.scrim
        autoclean_time = (
            (scrim.autoclean_time).strftime("%I:%M %p") if scrim.autoclean_time else "Not Set!"
        )

        embed = discord.Embed(color=config.COLOR)
        embed.title = "Edit Autoclean: {0}".format(scrim.id)
        description = "\n".join(
            f"{idx:02}. {(_type.value.title()).ljust(15)} {('❌', '✅')[_type in scrim.autoclean]}"
            for idx, _type in enumerate(constants.AutocleanType, start=1)
        )
        embed.description = f"```{description}```"
        embed.description += f"```03. Clean At: {autoclean_time}```"
        return embed

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.initial_embed())

    async def refresh(self):
        self.scrim = await Scrim.get(pk=self.scrim.id)
        await self.message.edit(embed=self.initial_embed())

    @menus.button(keycap_digit(1))
    async def on_one(self, payload):
        func = (ArrayAppend, ArrayRemove)[constants.AutocleanType.channel in self.scrim.autoclean]
        await Scrim.filter(pk=self.scrim.id).update(
            autoclean=func("autoclean", constants.AutocleanType.channel)
        )
        await self.refresh()

    @menus.button(keycap_digit(2))
    async def on_two(self, payload):
        func = (ArrayAppend, ArrayRemove)[constants.AutocleanType.role in self.scrim.autoclean]
        await Scrim.filter(pk=self.scrim.id).update(
            autoclean=func("autoclean", constants.AutocleanType.role)
        )
        await self.refresh()

    @menus.button(keycap_digit(3))
    async def on_three(self, payload):
        msg = await self.ctx.send(
            "**At what time should I run cleaner?**"
            "**Example: 14:00** - Registration will open at 2PM.\n\n"
            "**Currently Quotient works according to Indian Standard Time (UTC+05:30)**"
        )

        clean_time = await inputs.time_input(self.ctx, self.check, delete_after=True)
        await inputs.safe_delete(msg)

        await self.bot.get_cog("Reminders").create_timer(
            clean_time,
            "autoclean",
            scrim_id=self.scrim.id,
        )
        await Scrim.filter(pk=self.scrim.id).update(autoclean_time=clean_time)
        await self.refresh()

    @menus.button("\N{BLACK SQUARE FOR STOP}")
    async def on_stop(self, payload):
        self.stop()


class DaysMenu(menus.Menu):
    def __init__(self, *, scrim: Scrim):
        super().__init__(
            timeout=60,
            delete_message_after=False,
            clear_reactions_after=True,
        )
        self.scrim = scrim
        self.days = scrim.open_days
        self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

        # Adding buttons dynamically
        for idx, day in enumerate(constants.Day, start=1):

            def action(day):
                async def wraps(self, payload):
                    await self.update_scrim(day)

                return wraps

            self.add_button(Button(keycap_digit(idx), action(day)))

    def initial_embed(self):
        scrim = self.scrim
        embed = discord.Embed(color=discord.Color(config.COLOR))
        embed.title = "Edit Open Days: {0}".format(scrim.id)
        description = "\n".join(
            f"{idx:02}. {(day.value.title()).ljust(10)}   {('❌', '✅')[day in scrim.open_days]}"
            for idx, day in enumerate(constants.Day, start=1)
        )
        embed.description = f"```{description}```"
        return embed

    async def refresh(self):
        self.scrim = await Scrim.get(pk=self.scrim.id)
        await self.message.edit(embed=self.initial_embed())

    async def update_scrim(self, day):
        # Lets do some magic
        func = (ArrayAppend, ArrayRemove)[day in self.scrim.open_days]
        await Scrim.filter(pk=self.scrim.id).update(open_days=func("open_days", day))
        await self.refresh()

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.initial_embed())

    @menus.button("\N{BLACK SQUARE FOR STOP}\ufe0f")
    async def on_stop(self, payload):
        self.stop()


class ConfigEditMenu(menus.Menu):
    def __init__(self, *, scrim: Scrim):
        super().__init__(
            timeout=100,
            delete_message_after=False,
            clear_reactions_after=True,
        )
        self.scrim = scrim
        self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

    def initial_embed(self):
        scrim = self.scrim
        slotlist_channel = getattr(scrim.slotlist_channel, "mention", "`Channel Deleted!`")
        registration_channel = getattr(scrim.registration_channel, "mention", "`Channel Deleted!`")
        scrim_role = getattr(scrim.role, "mention", "`Role Deleted!`")
        open_time = (scrim.open_time).strftime("%I:%M %p")

        ping_role = scrim_work_role(scrim, constants.EsportsRole.ping)
        open_role = (
            getattr(scrim.open_role, "mention", "`Role Deleted!`")
            if scrim.open_role_id
            else "@everyone"
        )

        embed = discord.Embed(color=discord.Color(config.COLOR))
        embed.title = f"Edit Scrims Configuration: {scrim.id}"

        fields = {
            "Name": f"`{scrim.name}`",
            "Registration Channel": registration_channel,
            "Slotlist Channel": slotlist_channel,
            "Role": scrim_role,
            "Mentions": f"`{scrim.required_mentions:,}`",
            "Slots": f"`{scrim.total_slots:,}`",
            "Open Time": f"`{open_time}`",
            "Auto-clean": "`qsm autoclean {0}`".format(scrim.id),
            "Ping Role": ping_role,
            "Open Role": open_role,
            "Multi Register": ("`No!`", "`Yes!`")[scrim.multiregister],
            "Slotlist Start from": scrim.start_from,
            "Autodelete Rejected Registrations": ("`No!`", "`Yes!`")[scrim.autodelete_rejects],
            "Team Name compulsion": ("`No!`", "`Yes!`")[scrim.teamname_compulsion],
            "Duplicate Team Names": ("`Allowed!`", "`Not Allowed`")[scrim.no_duplicate_name],
        }

        for idx, (name, value) in enumerate(fields.items()):
            embed.add_field(
                name=f"{regional_indicator(string.ascii_uppercase[idx])} {name}:",
                value=value,
            )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        return embed

    async def cembed(self, description):
        return await self.ctx.send(
            embed=discord.Embed(
                color=discord.Color(config.COLOR),
                title=f"🛠️ Scrims Manager",
                description=description,
            )
        )

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.initial_embed())

    async def refresh(self):
        self.scrim = await Scrim.get(pk=self.scrim.id)
        await self.message.edit(embed=self.initial_embed())

    async def update_scrim(self, **kwargs):
        await Scrim.filter(pk=self.scrim.id).update(**kwargs)
        await self.refresh()

    @menus.button(regional_indicator("A"))
    async def change_scrim_name(self, payload):
        msg = await self.cembed("What is the new name you want to give to these scrims?")
        name = await inputs.string_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        if len(name) > 30:
            raise ScrimError("Scrims Name cannot exceed 30 characters.")
        elif len(name) < 5:
            raise ScrimError("The length of new name is too short.")

        await inputs.safe_delete(msg)
        await self.update_scrim(name=name)

    @menus.button(regional_indicator("B"))
    async def change_registration_channel(self, payload):
        msg = await self.cembed("Which is the new channel for registrations?")
        channel = await inputs.channel_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        await inputs.safe_delete(msg)
        await self.update_scrim(registration_channel_id=channel.id)

    @menus.button(regional_indicator("C"))
    async def change_slotlist_channel(self, payload):
        msg = await self.cembed("Which is the new channel for slotlists?")
        channel = await inputs.channel_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        await inputs.safe_delete(msg)
        await self.update_scrim(slotlist_channel_id=channel.id)

    @menus.button(regional_indicator("D"))
    async def change_scrim_role(self, payload):
        msg = await self.cembed("Which is the new role for correct registration?")
        role = await inputs.role_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        await inputs.safe_delete(msg)
        await self.update_scrim(role_id=role.id)

    @menus.button(regional_indicator("E"))
    async def change_required_mentions(self, payload):
        msg = await self.cembed("How many mentions are required for successful registration?")
        mentions = await inputs.integer_input(
            self.ctx,
            self.check,
            delete_after=True,
            limits=(0, 10),
        )
        await inputs.safe_delete(msg)
        await self.update_scrim(required_mentions=mentions)

    @menus.button(regional_indicator("F"))
    async def change_total_slots(self, payload):
        msg = await self.cembed("How many total slots are there?")
        slots = await inputs.integer_input(
            self.ctx,
            self.check,
            delete_after=True,
            limits=(1, 30),
        )
        await inputs.safe_delete(msg)
        await self.update_scrim(total_slots=slots)

    @menus.button(regional_indicator("G"))
    async def change_open_time(self, payload):
        msg = await self.cembed(
            "**At what time should I open registrations?**"
            "**Example: 14:00** - Registration will open at 2PM.\n\n"
            "**Currently Quotient works according to Indian Standard Time (UTC+05:30)**"
        )

        open_time = await inputs.time_input(self.ctx, self.check, delete_after=True)
        await inputs.safe_delete(msg)

        await self.bot.get_cog("Reminders").create_timer(
            open_time,
            "scrim_open",
            scrim_id=self.scrim.id,
        )

        await self.update_scrim(open_time=open_time)

    @menus.button(regional_indicator("H"))
    async def change_cleanup(self, payload):
        pass

    @menus.button(regional_indicator("I"))
    async def change_ping_role(self, payload):
        msg = await self.cembed("Which role should I ping when I open registrations?")

        role = await inputs.role_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        await inputs.safe_delete(msg)
        await self.update_scrim(ping_role_id=role.id)

    @menus.button(regional_indicator("J"))
    async def change_open_role(self, payload):
        msg = await self.cembed("For which role should I open registrations?")

        role = await inputs.role_input(
            self.ctx,
            self.check,
            delete_after=True,
        )

        await inputs.safe_delete(msg)
        await self.update_scrim(open_role_id=role.id)

    @menus.button(regional_indicator("K"))
    async def change_multiregister(self, payload):
        await self.ctx.success(
            f"Multiple registrations from a single user are now **{'Allowed' if not self.scrim.multiregister else 'Not Allowed'}!**",
            delete_after=3,
        )
        await self.update_scrim(multiregister=not self.scrim.multiregister)

    @menus.button(regional_indicator("L"))
    async def change_start_from(self, payload):
        m = await self.ctx.send(
            "From which slot do you want me to start slotlist?\n\nThis can be any number between 1 and 20."
        )
        start_from = await inputs.integer_input(
            self.ctx,
            self.check,
            delete_after=True,
            limits=(1, self.scrim.total_slots),
        )

        await inputs.safe_delete(m)
        await self.update_scrim(start_from=start_from)

    @menus.button(regional_indicator("M"))
    async def auto_delete_rejects(self, payload):
        await self.ctx.success(
            f"Rejected registrations will **{'NOW' if not self.scrim.autodelete_rejects else 'NOT'}** be deleted.",
            delete_after=2,
        )
        await self.update_scrim(autodelete_rejects=not self.scrim.autodelete_rejects)

    @menus.button(regional_indicator("N"))
    async def teamname_compulsory(self, payload):
        await self.ctx.success(
            f"Team name in registrations is now **{'Necessary' if not self.scrim.teamname_compulsion else 'Not Necessary'}!**",
            delete_after=2,
        )
        await self.update_scrim(teamname_compulsion=not self.scrim.teamname_compulsion)

    @menus.button(regional_indicator("O"))
    async def _no_team_name(self, payload):
        await self.ctx.success(
            f"Duplicate team names are not **{'Allowed' if self.scrim.no_duplicate_name else 'Not Allowed'}!**",
            delete_after=2,
        )
        await self.update_scrim(no_duplicate_name=not self.scrim.no_duplicate_name)

    @menus.button("\N{BLACK SQUARE FOR STOP}\ufe0f")
    async def on_stop(self, payload):
        self.stop()
