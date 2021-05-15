from discord.ext.commands.cooldowns import BucketType
from models import AssignedSlot, Scrim, Timer
from datetime import timedelta, datetime
from discord import AllowedMentions
from dataclasses import dataclass
from discord.ext import commands
from utils import default, time
from utils.constants import IST
from .utils import ConfigEditMenu
from .errors import ScrimError, SMError
from utils import inputs
from core import Cog

import discord
import asyncio
import config


@dataclass
class QueueMessage:
    scrim: Scrim
    message: discord.Message

    def __iter__(self):
        return iter((self.scrim, self.message))


class ScrimManager(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = asyncio.Queue()
        self.bot.loop.create_task(self.fill_registration_channels())
        self.bot.loop.create_task(self.registration_worker())

    async def fill_registration_channels(self):
        records = Scrim.filter(opened_at__lte=datetime.now(tz=IST)).all()
        self.registration_channels = set()

        async for record in records:
            self.registration_channels.add(record.registration_channel_id)

    async def registration_worker(self):
        while True:
            queue_message: QueueMessage = await self.queue.get()
            scrim, message = queue_message

            ctx = await self.bot.get_context(message)

            matched_lines = tuple(
                line.strip()
                for line in ctx.message.clean_content.lower().split("\n")
                if "team" in line
            )

            if len(matched_lines) == 0:
                teamname = f"{str(ctx.author)}'s team"
            else:
                teamname = default.find_team(matched_lines)

            scrim = await Scrim.get_or_none(
                pk=scrim.id
            )  # Refetch Scrim to check get its updated instance...

            if not scrim or scrim.closed:  # Scrim is deleted or not opened yet.
                continue

            print("scrims not closed")
            assigned_slots = await scrim.assinged_slots.all().count()

            slot = await AssignedSlot.create(
                id=scrim.id,
                user_id=ctx.author.id,
                team_name=teamname,
                num=assigned_slots + 1,
                jump_url=message.jump_url,
            )

            await scrim.assinged_slots.add(slot)
            await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

            if scrim.total_slots == assigned_slots + 1:
                await Scrim.filter(pk=scrim.id).update(closed_at=datetime.now(tz=IST))

                registration_channel = scrim.registration_channel
                overwrite = registration_channel.overwrites_for(ctx.guild.default_role)
                overwrite.update(send_messages=True)
                await registration_channel.set_permissions(
                    ctx.guild.default_role,
                    overwrite=overwrite,
                    reason="Open for scrim registration!",
                )
                await ctx.send("Registration is now closed.")

    @property
    def reminders(self):
        return self.bot.get_cog("Reminders")

    # ************************************************************************************************

    @commands.Cog.listener()
    async def on_scrim_open_timer_complete(self, timer: Timer):
        """This listener opens the scrim registration at time."""
        scrim_id = timer.kwargs["scrim_id"]
        scrim = await Scrim.get(pk=scrim_id)

        if scrim.open_time != timer.expires:  # If time is not same return :)
            return

        if scrim.toggle != True or not hasattr(scrim.open_days, time.day_today()):
            return await self.SMNotToday(scrim, timer)

        guild = scrim.guild

        if guild is None:
            return await scrim.delete()

        if scrim.registration_channel is None:  # Error tum hi dispatch karlio
            pass

        if scrim.role is None:  # Error tum hi dispatch karlio
            pass

        if scrim.open_role_id and not scrim.open_role:  # Error tum hi dispatch karlio
            pass

        scrim_open_role = scrim.open_role or guild.default_role

        if scrim.ping_role_id and not scrim.ping_role:
            pass  # Error tum hi dispatch karlio

        scrim_ping_role = scrim.ping_role

        reserved_count = await scrim.reserved_slots.all().count()

        embed = discord.Embed(
            color=discord.Color(config.COLOR),
            title="Registration is now open!",
            description=f"📣 **`{scrim.required_mentions}`** mentions required.\n"
            f"📣 Total slots: **`{scrim.total_slots}`** [`{reserved_count}` slots reserved]",
        )

        await scrim.assinged_slots.clear()  # Deleting all previously assigned slots. (idk why this line exists.)

        async for slot in scrim.reserved_slots.all():
            count = await scrim.assinged_slots.all().count()

            assinged_slot = AssignedSlot.create(
                user_id=slot.user_id,
                team_name=slot.team_name,
                members=slot.members,
                jump_url=None,
                num=count + 1,
            )

            await scrim.assinged_slots.add(assinged_slot)

            self.bot.loop.create_task(
                guild.get_member(slot.user_id).add_roles(scrim.role),
            )

        # Opening Channel for Normal Janta
        registration_channel = scrim.registration_channel
        overwrite = registration_channel.overwrites_for(scrim_open_role)
        overwrite.update(send_messages=True)
        await registration_channel.set_permissions(
            scrim_open_role,
            overwrite=overwrite,
            reason="Open for scrim registration!",
        )

        self.registration_channels.add(registration_channel.id)

        await Scrim.filter(pk=scrim.id).update(
            open_time=scrim.open_time + timedelta(hours=24),
            opened_at=datetime.now(tz=IST),
            closed_at=None,
        )

        await scrim.refresh_from_db(("open_time",))

        # Creating a new Reminder
        await self.reminders.create_timer(
            scrim.open_time,
            "scrim_open",
            scrim_id=scrim.id,
        )

        await registration_channel.send(
            content=getattr(scrim_ping_role, "mention", None),
            embed=embed,
            allowed_mentions=AllowedMentions(roles=True, everyone=True),
        )

        log_channel = discord.utils.get(
            guild.text_channels,
            name="quotient-scrims-logs",
        )

        if log_channel is not None:
            embed = discord.Embed(
                color=0x00B1FF,
                description=f"Registration opened for {scrim_open_role.mention} in {registration_channel.mention}(ScrimsID: `{scrim.id}`)",
            )

        else:  # Error khudhi dispatch kar lena
            pass

    # ************************************************************************************************

    @commands.group(aliases=("s",))
    async def smanager(self, ctx):
        pass

    async def cog_command_error(self, ctx, error):
        if isinstance(error, ScrimError):
            return await ctx.send(error)

        raise error

    def config_embed(self, value, description: str):
        embed = discord.Embed(
            color=discord.Color(config.COLOR),
            title=f"🛠️ Scrims Manager ({value}/6)",
            description=description,
        )
        embed.set_footer(text=f'Reply with "cancel" to stop the process.')
        return embed

    # ************************************************************************************************

    @smanager.command()
    @commands.max_concurrency(1, BucketType.guild)
    async def setup(self, ctx):

        count = await Scrim.filter(guild_id=ctx.guild.id).count()

        if count > 3:
            raise ScrimError("You can't host more than 3 scrims concurrently.")

        def check(message: discord.Message):
            if message.content.strip().lower() == "cancel":
                raise ScrimError("Alright, reverting all process.")

            return message.author == ctx.author and ctx.channel == message.channel

        # Registration Channel.
        scrim = Scrim(
            guild_id=ctx.guild.id,
            host_id=ctx.author.id,
        )
        await ctx.send(
            embed=self.config_embed(
                1,
                "Which is the default registration channel?",
            )
        )
        channel = await inputs.channel_input(ctx, check)

        if await Scrim.filter(registration_channel_id=channel.id).count():
            raise ScrimError("This channel is already a registration channel.")

        scrim.registration_channel_id = channel.id

        # Slotlist Channel
        await ctx.send(
            embed=self.config_embed(
                2,
                f"Which is default slotlist channel for {scrim.registration_channel.mention}?",
            )
        )

        channel = await inputs.channel_input(ctx, check)

        scrim.slotlist_channel_id = channel.id

        # Role (Registered Users)
        await ctx.send(
            embed=self.config_embed(
                3,
                f"What role should I give for correct registration?",
            )
        )

        role = await inputs.role_input(ctx, check)

        scrim.role_id = role.id

        # Mentions Limit

        await ctx.send(
            embed=self.config_embed(
                4,
                "How many mentions are required for successful registration?"
                " (Can't be more than 10 or less than 1.)",
            )
        )

        scrim.required_mentions = await inputs.integer_input(
            ctx,
            check,
            limits=(1, 10),
        )

        # Total Slots

        await ctx.send(
            embed=self.config_embed(
                5,
                "How many total slots are there? (Can't be more than 30 or less than 1.)",
            )
        )

        scrim.total_slots = await inputs.integer_input(
            ctx,
            check,
            limits=(1, 30),
        )

        await ctx.send(
            embed=self.config_embed(
                6,
                "**At what time should I open registrations?**"
                "\n> Time must be in 24h and in this format **`hh:mm`**\n"
                "**Example: 14:00** - Registration will open at 2PM.\n\n"
                "**Currently Quotient works according to Indian Standard Time (UTC+05:30)**",
            )
        )
        scrim.open_time = await inputs.time_input(ctx, check)

        registration_channel = scrim.registration_channel

        fields = [
            f"Registration Channel: {registration_channel.mention}",
            f"Slotlist Channel: {scrim.slotlist_channel.mention}",
            f"Role: {scrim.role.mention}",
            f"Minimum Mentions: {scrim.required_mentions}",
            f"Slots: {scrim.total_slots}",
            f"Open Time: {time(scrim.open_time)}",
        ]

        title = ("Are these correct?",)
        description = "\n".join(
            f"`{idx}.` {field}" for idx, field in enumerate(fields, start=1)
        )

        confirm = await ctx.prompt(description, title=title)
        confirm = True
        if not confirm:
            await ctx.send("Ok, Aborting!")
        else:
            message = await ctx.send("Setting up everything!")
            reason = "Created for scrims management."

            # Scrims MODS
            scrims_mod = discord.utils.get(ctx.guild.roles, name="scrims-mod")

            if scrims_mod is None:
                scrims_mod = await ctx.guild.create_role(
                    name="scrims-mod", color=0x00FFB3, reason=reason
                )

            overwrite = registration_channel.overwrites_for(ctx.guild.default_role)
            overwrite.update(
                read_messages=True, send_messages=True, read_message_history=True
            )
            await registration_channel.set_permissions(scrims_mod, overwrite=overwrite)

            # Srims LOGS
            scrims_log_channel = discord.utils.get(
                ctx.guild.text_channels, name="quotient-scrims-logs"
            )

            if scrims_log_channel is None:
                guild = ctx.guild
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        read_messages=False
                    ),
                    guild.me: discord.PermissionOverwrite(read_messages=True),
                    scrims_mod: discord.PermissionOverwrite(read_messages=True),
                }
                scrims_log_channel = await ctx.guild.create_text_channel(
                    name="quotient-scrims-logs",
                    overwrites=overwrites,
                    reason=reason,
                )

                # Sending Message to scrims-log-channel
                note = await scrims_log_channel.send(
                    embed=discord.Embed(
                        description=f"If events related to scrims i.e opening registrations or adding roles, "
                        f"etc are triggered, then they will be logged in this channel. "
                        f"Also I have created {scrims_mod.mention}, you can give that role to your "
                        f"scrims-moderators. User with {scrims_mod.mention} can also send messages in "
                        f"registration channels and they won't be considered as scrims-registration.\n\n"
                        f"`Note`: **Do not rename this channel.**",
                        color=discord.Color(config.COLOR),
                    )
                )
                await note.pin()

            await scrim.save()
            await self.reminders.create_timer(
                scrim.open_time, "scrim_open", scrim_id=scrim.id
            )
            text = f"Scrims Management Setup Complete. (`Scrims ID: {scrim.id}`)"
            try:
                await message.edit(content=text)
            except discord.NotFound:
                await ctx.send(text)

    @smanager.command()
    async def edit(self, ctx, *, scrim_id: int):
        scrim = await Scrim.get_or_none(pk=scrim_id, guild_id=ctx.guild.id)
        if scrim is None:
            raise ScrimError(
                "This Scrim doesn't seems to exists or not belongs to your server."
            )
        menu = ConfigEditMenu(scrim=scrim)
        await menu.start(ctx)

    @commands.Cog.listener("on_message")
    async def on_scrim_registration(self, message: discord.Message):
        # if not message.guild or message.author.bot:
        #     return
        if message.author == self.bot.user:
            return

        channel_id = message.channel.id

        if channel_id not in self.registration_channels:
            return

        scrim = await Scrim.get_or_none(
            registration_channel_id=channel_id,
        )

        if scrim is None:  # Scrim is possibly deleted
            self.registration_channels.pop(channel_id)
            return

        if scrim.opened_at is None:
            # Registration isn't opened yet.
            return

        # if not all(map(lambda m: not m.bot, message.mentions)):
        #     # Mentioned Bots
        #     return

        self.queue.put_nowait(QueueMessage(scrim, message))


def setup(bot):
    bot.add_cog(ScrimManager(bot))
    bot.add_cog(SMError(bot))
