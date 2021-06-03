import json, aiohttp
import config
from discord.ext import menus
from discord.ext.menus import Button
import string
from models import Scrim, AssignedSlot, Tourney
from models.esports import ReservedSlot
from utils import *
from models.functions import *
import constants
from .errors import ScrimError, TourneyError
from .utils import already_reserved, available_to_reserve


class SlotlistFormatMenu(menus.Menu):
    def __init__(self, scrim: Scrim):
        super().__init__(
            timeout=60,
            delete_message_after=False,
            clear_reactions_after=True,
        )
        self.scrim = scrim
        self.msg = None
        self.cur_embed = discord.Embed()

        self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

    def initial_embed(self):
        if self.scrim.slotlist_format:
            edict = json.loads(self.scrim.slotlist_format)
            embed = discord.Embed.from_dict(edict)

        else:
            embed = discord.Embed()

        slotstr = "```Slot No.  -->  Team Name\n```"
        embed.description = f"{slotstr * 5}\n\n{embed.description if embed.description else ''}"

        return embed

    def desc_embed(self):
        embed = discord.Embed(title="Slotlist Format Editor", color=config.COLOR)
        embed.description = (
            "🇹 | Set Title\n"
            "🇩 | Set Description\n"
            "🇫 | Set Footer\n"
            "🌈 | Set embed color \n"
            "🖼️ | Set Image\n"
            "📸 | Set Thumbnail\n"
            "❌ | Don't Save and Abort\n"
            "✅ | Save and Abort\n"
        )
        return embed

    async def send_initial_message(self, ctx, channel):
        self.cur_embed = self.initial_embed()
        self.msg = await channel.send(embed=self.cur_embed)
        return await channel.send(embed=self.desc_embed())

    async def refresh(self):
        try:
            await self.msg.edit(embed=self.cur_embed)
        except:
            self.stop()

    async def cembed(self, description):
        return await self.ctx.send(
            embed=discord.Embed(
                color=discord.Color(config.COLOR),
                title=f"🛠️ Scrims Manager",
                description=description,
            ).set_footer(text="Enter 'none' if you want to remove the field.")
        )

    @menus.button(regional_indicator("T"))
    async def set_title(self, payload):
        msg = await self.cembed(f"What do you want the title to be?\n\nTitle cannot exceed 256 characters.")

        title = await inputs.string_input(self.ctx, self.check, delete_after=True)
        if len(title) > 256:
            return await self.ctx.error(f"Title cannot exceed 256 characters.", delete_after=3)

        await inputs.safe_delete(msg)
        if title.lower() == "none":
            self.cur_embed.title = discord.Embed.Empty
        else:
            self.cur_embed.title = title
        await self.refresh()

    @menus.button(regional_indicator("D"))
    async def set_description(self, payload):
        msg = await self.cembed(
            f"What do you want the description to be?\n\n This will be added below the slotlist. This cannot exceed 1000 characters."
        )

        description = await inputs.string_input(self.ctx, self.check, delete_after=True)

        if len(description) > 1000:
            return await self.ctx.error(f"Description cannot contain more than 1000 characters.", delete_after=3)

        await inputs.safe_delete(msg)

        if description.lower() == "none":
            self.cur_embed.description = "```Slot No.  -->  Team Name\n```" * 5

        self.cur_embed.description += description
        await self.refresh()

    @menus.button(regional_indicator("F"))
    async def set_footer(self, payload):
        msg = await self.cembed(f"What do you want the footer text to be?\n\nThis cannot exceed 2048 characters.")
        footer = await inputs.string_input(self.ctx, self.check, delete_after=True)

        await inputs.safe_delete(msg)

        if footer.lower() == "none":
            self.cur_embed.set_footer(text=discord.Embed.Empty)

        else:
            self.cur_embed.set_footer(text=footer)

        await self.refresh()

    @menus.button("🌈")
    async def set_color(self, payload):
        msg = await self.cembed(f"What color do you want to give the embed?")
        color = await inputs.string_input(self.ctx, self.check, delete_after=True)
        await inputs.safe_delete(msg)

        color = await ColorConverter().convert(self.ctx, color)
        self.cur_embed.color = color
        await self.refresh()

    @menus.button("🖼️")
    async def add_image(self, payload):
        msg = await self.cembed(f"Enter the Image URL you want to set.")
        image = await inputs.string_input(self.ctx, self.check, delete_after=True)

        await inputs.safe_delete(msg)

        if image.lower() == "none":
            self.cur_embed.set_image(url=discord.Embed.Empty)
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
                return await self.ctx.error(f"The URL didn't contain a valid Image format.", delete_after=3)
            self.cur_embed.set_image(url=image)
            await self.refresh()

    @menus.button("📸")  # a lot of redundancy? yes, will deal with later
    async def add_thumbnail(self, payload):
        msg = await self.cembed(f"Enter the Image URL you want to set as thumbnail.")
        image = await inputs.string_input(self.ctx, self.check, delete_after=True)

        await inputs.safe_delete(msg)

        if image.lower() == "none":
            self.cur_embed.set_image(url=discord.Embed.Empty)
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
                return await self.ctx.error(f"The URL didn't contain a valid Image format.", delete_after=3)

            self.cur_embed.set_thumbnail(url=image)
            await self.refresh()

    @menus.button("❌")
    async def donot_save(self, payload):
        self.stop()

    @menus.button("✅")
    async def save_and_abort(self, payload):
        self.cur_embed.description = self.cur_embed.description.replace("```Slot No.  -->  Team Name\n```" * 5, "")
        edict = self.cur_embed.to_dict()

        await Scrim.filter(id=self.scrim.id).update(slotlist_format=str(edict))

        await self.ctx.success(f"Updated the slotlist format.", delete_after=3)

        self.stop()


class ReserveEditorMenu(menus.Menu):
    def __init__(self, *, scrim: Scrim):
        super().__init__(
            timeout=60,
            delete_message_after=False,
            clear_reactions_after=True,
        )
        self.scrim = scrim
        self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

    async def initial_embed(self):
        reserves = await self.scrim.reserved_slots.all()
        embed = discord.Embed(color=self.bot.color)

        to_show = []
        for i in self.scrim.available_to_reserve:
            check = [j.team_name for j in reserves if j.num == i]

            if len(check):
                info = check[0]
            else:
                info = "❌"

            to_show.append(f"Slot {i:02}  -->  {info}\n")

        embed.description = f"```{''.join(to_show)}```\n\n{emote.add} | Reserve a slot\n{emote.remove} | Remove a reserved slot\n🔢 | Edit the first slot number\n✅ | Save and Abort"

        return embed

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=await self.initial_embed())

    async def refresh(self):
        self.scrim = await Scrim.get(pk=self.scrim.id)
        await self.message.edit(embed=await self.initial_embed())

    @menus.button(emote.add)
    async def reserve_a_slot(self, payload):
        available = await available_to_reserve(self.scrim)
        if not len(available):
            return await self.ctx.error("No slots left to reserve.", delete_after=3)

        msg = await self.ctx.send(
            f"Which slot do you wish to reserve? Choose from:\n\n{', '.join(map(lambda x: f'`{x}`', available))}"
        )
        to_reserve = await inputs.integer_input(
            self.ctx,
            self.check,
            delete_after=True,
            limits=(None, None),
        )

        await inputs.safe_delete(msg)

        if to_reserve not in available:
            return await self.ctx.error(f"You cannot reserve this slot.", delete_after=3)

        msg = await self.ctx.send(
            "For which user do you wish to reserve a slot?\nThis is needed to add scrims role to them when registration start.",
        )

        member = await inputs.member_input(self.ctx, self.check, delete_after=True)
        if not member:
            return await self.ctx.error(f"That's not a valid member.", delete_after=3)

        if member.id in await self.scrim.reserved_user_ids():
            return await self.ctx.error(f"{str(member)} is already in the reserved list.", delete_after=3)

        await inputs.safe_delete(msg)

        msg = await self.ctx.send(f"What is {member}'s team name?")
        team_name = await inputs.string_input(self.ctx, self.check, delete_after=True)

        await inputs.safe_delete(msg)

        msg = await self.ctx.send(
            "For how much time should I reserve the slot for them?\n\nEnter `none` if you don't want to set time."
        )
        duration = await inputs.string_input(self.ctx, self.check, delete_after=True)
        if not duration.lower() == "none":
            duration = FutureTime(duration)
            future = duration.dt

        else:
            future = None

        await inputs.safe_delete(msg)
        slot = await ReservedSlot.create(num=to_reserve, user_id=member.id, team_name=team_name, expires=future)
        await self.scrim.reserved_slots.add(slot)

        if future:
            print(duration.dt)
            await self.ctx.bot.reminders.create_timer(
                future, "scrim_reserve", scrim_id=self.scrim.id, user_id=member.id, team_name=team_name, num=to_reserve
            )

        await self.refresh()

    @menus.button(emote.remove)
    async def remove_reserved_slot(self, payload):
        available = await already_reserved(self.scrim)
        if not len(available):
            return await self.ctx.error("There are 0 reserved slots.", delete_after=3)

        msg = await self.ctx.send(
            f"Which slot do you wish to remove from reserved? Choose from:\n\n{', '.join(map(lambda x: f'`{x}`', available))}"
        )
        slot = await inputs.integer_input(
            self.ctx,
            self.check,
            delete_after=True,
            limits=(None, None),
        )

        await inputs.safe_delete(msg)

        if slot not in available:
            return await self.ctx.error(f"This is not a reserved slot.", delete_after=3)

        slot = await self.scrim.reserved_slots.filter(num=slot).first()
        await ReservedSlot.filter(id=slot.id).delete()
        await self.refresh()

    @menus.button("🔢")
    async def edit_start_from(self, payload):
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
        await Scrim.filter(id=self.scrim.id).update(start_from=start_from)
        await self.refresh()

    @menus.button("✅")
    async def on_save(self, payload):
        self.stop()


class Points(menus.Menu):
    def __init__(self, *, scrim: Scrim):
        super().__init__(
            timeout=60,
            delete_message_after=False,
            clear_reactions_after=True,
        )
        self.scrim = scrim
        self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

    # will create live points tables
    ...


class SlotEditor(menus.Menu):
    def __init__(self, *, scrim: Scrim):
        super().__init__(
            timeout=60,
            delete_message_after=False,
            clear_reactions_after=True,
        )
        self.scrim = scrim
        self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

    async def initial_embed(self):
        embed, channel = await self.scrim.create_slotlist()
        embed.color = config.COLOR
        embed.description += f"\n\n\N{BLACK SQUARE FOR STOP}\ufe0f | Remove changes and Abort.\n{keycap_digit(1)} | Change a slot.\n{keycap_digit(2)} | Insert one more slot.\n✅ | Send And Exit."

        return embed

    async def refresh(self):
        self.scrim = await Scrim.get(pk=self.scrim.id)
        await self.message.edit(embed=await self.initial_embed())

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=await self.initial_embed())

    @menus.button("\N{BLACK SQUARE FOR STOP}\ufe0f")
    async def on_stop(self, payload):
        self.stop()

    @menus.button(keycap_digit(1))
    async def on_one(self, payload):
        msg = await self.ctx.send(embed=discord.Embed(color=config.COLOR, description=f"Which slot do you want to edit?"))
        slot = await inputs.integer_input(
            self.ctx,
            self.check,
            delete_after=True,
            limits=(None, None),
        )

        await inputs.safe_delete(msg)
        slots = await self.scrim.assigned_slots.filter(num=slot).first()
        if not slots:
            await self.ctx.send(
                e=discord.Embed(color=discord.COLOR.red(), description="You entered an invalid slot number."),
                delete_after=2,
            )
            await self.refresh()

        else:

            msg = await self.ctx.send(
                embed=discord.Embed(
                    color=config.COLOR, description=f"Enter the team name to which you want to give this slot?"
                )
            )
            teamname = await inputs.string_input(self.ctx, self.check, delete_after=True)

            await inputs.safe_delete(msg)

            await AssignedSlot.filter(id=slots.id).update(team_name=teamname)
            await self.refresh()

    @menus.button(keycap_digit(2))
    async def on_two(self, payload):
        msg = await self.ctx.send(embed=discord.Embed(color=config.COLOR, description="Enter new team's name."))
        teamname = await inputs.string_input(self.ctx, self.check, delete_after=True)
        await inputs.safe_delete(msg)

        assigned_slots = await self.scrim.assigned_slots.order_by("-num").first()
        slot = await AssignedSlot.create(
            user_id=self.ctx.author.id,
            team_name=teamname,
            num=assigned_slots.num + 1,
            jump_url=self.ctx.message.jump_url,
        )

        await self.scrim.assigned_slots.add(slot)
        await self.refresh()

    @menus.button("✅")
    async def on_check(self, payload):
        embed, channel = await self.scrim.create_slotlist()
        embed.color = config.COLOR
        if not channel:
            await self.ctx.error("I couldn't find slotlist channel.")

        elif self.scrim.slotlist_message_id != None:
            slotmsg = channel.get_partial_message(self.scrim.slotlist_message_id)

            if slotmsg:
                await slotmsg.edit(embed=embed)

            else:
                await channel.send(embed=embed)

        else:
            await channel.send(embed=embed)

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

        ping_role = getattr(scrim.ping_role, "mention", "`Role Deleted!`") if scrim.ping_role_id else "`Not Configured!`"
        open_role = getattr(scrim.open_role, "mention", "`Role Deleted!`") if scrim.open_role_id else "@everyone"

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
            "Auto-clean": ("`No!`", "`Yes!`")[scrim.autoclean],
            "Ping Role": ping_role,
            "Open Role": open_role,
            "Multi Register": ("`No!`", "`Yes!`")[scrim.multiregister],
            "Slotlist Start from": scrim.start_from,
        }

        for idx, (name, value) in enumerate(fields.items()):
            embed.add_field(
                name=f"{regional_indicator(string.ascii_uppercase[idx])} {name}:",
                value=value,
            )

        embed.set_thumbnail(url=self.bot.user.avatar_url)
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
            "\n> Time must be in 24h and in this format **`hh:mm`**\n"
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
        await self.update_scrim(autoclean=not self.scrim.autoclean)

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

    @menus.button("\N{BLACK SQUARE FOR STOP}\ufe0f")
    async def on_stop(self, payload):
        self.stop()


class TourneyEditor(menus.Menu):
    def __init__(self, *, tourney: Tourney):
        super().__init__(
            timeout=100,
            delete_message_after=False,
            clear_reactions_after=True,
        )
        self.tourney = tourney
        self.check = lambda msg: msg.channel == self.ctx.channel and msg.author == self.ctx.author

    def initial_embed(self):
        tourney = self.tourney
        slotlist_channel = getattr(tourney.confirm_channel, "mention", "`Channel Deleted!`")
        registration_channel = getattr(tourney.registration_channel, "mention", "`Channel Deleted!`")
        tourney_role = getattr(tourney.role, "mention", "`Role Deleted!`")

        open_role = getattr(tourney.open_role, "mention", "`Role Deleted!`")

        embed = self.bot.embed(self.ctx)
        embed.title = f"Edit Tourney Configuration: {tourney.id}"

        fields = {
            "Name": f"`{tourney.name}`",
            "Registration Channel": registration_channel,
            "Slotlist Channel": slotlist_channel,
            "Role": tourney_role,
            "Mentions": f"`{tourney.required_mentions:,}`",
            "Slots": f"`{tourney.total_slots:,}`",
            "Open Role": open_role,
            "Multi Register": ("`No!`", "`Yes!`")[tourney.multiregister],
        }

        for idx, (name, value) in enumerate(fields.items()):
            embed.add_field(
                name=f"{regional_indicator(string.ascii_uppercase[idx])} {name}:",
                value=value,
            )

        embed.set_thumbnail(url=self.bot.user.avatar_url)
        return embed

    async def cembed(self, description):
        return await self.ctx.send(
            embed=discord.Embed(
                color=discord.Color(config.COLOR),
                title=f"🛠️ Tourney Manager",
                description=description,
            )
        )

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.initial_embed())

    async def refresh(self):
        self.tourney = await Tourney.get(pk=self.tourney.id)
        await self.message.edit(embed=self.initial_embed())

    async def update_tourney(self, **kwargs):
        await Tourney.filter(pk=self.tourney.id).update(**kwargs)
        await self.refresh()

    @menus.button(regional_indicator("A"))
    async def change_tourney_name(self, payload):
        msg = await self.cembed("What is the new name you want to give to the tournament?")
        name = await inputs.string_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        if len(name) > 200:
            raise TourneyError("Tournament Name cannot exceed 30 characters.")
        elif len(name) < 5:
            raise TourneyError("The length of new name is too short.")

        await inputs.safe_delete(msg)
        await self.update_tourney(name=name)

    @menus.button(regional_indicator("B"))
    async def change_registration_channel(self, payload):
        msg = await self.cembed("Which is the new channel for registrations?")
        channel = await inputs.channel_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        await inputs.safe_delete(msg)
        await self.update_tourney(registration_channel_id=channel.id)

    @menus.button(regional_indicator("C"))
    async def change_slotlist_channel(self, payload):
        msg = await self.cembed("Which is the new channel for slotlists?")
        channel = await inputs.channel_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        await inputs.safe_delete(msg)
        await self.update_tourney(slotlist_channel_id=channel.id)

    @menus.button(regional_indicator("D"))
    async def change_tourney_role(self, payload):
        msg = await self.cembed("Which is the new role for correct registration?")
        role = await inputs.role_input(
            self.ctx,
            self.check,
            delete_after=True,
        )
        await inputs.safe_delete(msg)
        await self.update_tourney(role_id=role.id)

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
        await self.update_tourney(required_mentions=mentions)

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
        await self.update_tourney(total_slots=slots)

    @menus.button(regional_indicator("G"))
    async def change_open_role(self, payload):
        msg = await self.cembed("For which role should I open registrations?")

        role = await inputs.role_input(
            self.ctx,
            self.check,
            delete_after=True,
        )

        await inputs.safe_delete(msg)
        await self.update_tourney(open_role_id=role.id)

    @menus.button(regional_indicator("H"))
    async def change_multiregister(self, payload):
        await self.update_tourney(multiregister=not self.tourney.multiregister)

    @menus.button("\N{BLACK SQUARE FOR STOP}\ufe0f")
    async def on_stop(self, payload):
        self.stop()
