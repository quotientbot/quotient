import discord
from tortoise import fields
from tortoise.contrib.postgres.fields import ArrayField

from quotient.models import BaseDbModel


class Tourney(BaseDbModel):
    class Meta:
        table = "tournaments"

    id = fields.IntField(primary_key=True, db_index=True)
    guild_id = fields.BigIntField()
    name = fields.CharField(max_length=30, default="Quotient-Tourney")
    registration_channel_id = fields.BigIntField()
    confirm_channel_id = fields.BigIntField()
    success_role_id = fields.BigIntField()

    required_mentions = fields.SmallIntField(default=4)
    total_slots = fields.SmallIntField(default=100)

    banned_user_ids = ArrayField("BIGINT", default=list)
    allow_multiple_registrations = fields.BooleanField(default=True)
    allow_without_teamname = fields.BooleanField(default=False)
    allow_duplicate_teamname = fields.BooleanField(default=True)  # whether same team name can be used multiple times
    allow_duplicate_mentions = fields.BooleanField(default=True)  # whether same user can be mentioned in multiple regs
    autodelete_rejected_registrations = fields.BooleanField(default=False)
    required_lines = fields.SmallIntField(default=0)

    started_at = fields.DatetimeField(null=True)
    ended_at = fields.DatetimeField(null=True)

    reg_start_ping_role_id = fields.BigIntField(null=True)
    grouplist_start_from = fields.SmallIntField(default=1)
    group_size = fields.SmallIntField(default=10)

    registration_success_dm_msg = fields.CharField(max_length=2000, null=True)
    reactions = ArrayField("VARCHAR(50)", default=lambda: list(["✅", "❌"]))

    slotm_channel_id = fields.BigIntField()
    slotm_message_id = fields.BigIntField()

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    assigned_slots: fields.ReverseRelation["TourneyAssignedSlot"]

    def __str__(self):
        return f"{getattr(self.registration_channel,'mention','deleted-channel')} (ID: {self.id})"

    @staticmethod
    def is_ignorable(member: discord.Member) -> bool:
        """
        If the member has `tourney-mod` role, they can be ignored in registration channels.
        """
        return "tourney-mod" in (role.name.lower() for role in member.roles)

    @property
    def guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def registration_channel(self):
        return self.guild.get_channel(self.registration_channel_id)

    @property
    def confirm_channel(self):
        return self.guild.get_channel(self.confirm_channel_id)

    @property
    def success_role(self):
        return self.guild.get_role(self.success_role_id)

    @property
    def reg_start_ping_role(self):
        return self.guild.get_role(self.reg_start_ping_role_id)

    @property
    def tourney_mod_role(self):
        return discord.utils.get(self.guild.roles, name="tourney-mod")

    @property
    def logs_channel(self):
        return discord.utils.get(self.guild.text_channels, name="quotient-tourney-logs")

    @property
    def tick_emoji(self):
        try:
            return self.reactions[0]
        except IndexError:
            return "✅"

    @property
    def cross_emoji(self):
        try:
            return self.reactions[1]
        except IndexError:
            return "❌"

    @property
    def start_ping_role(self):
        return self.guild.get_role(self.reg_start_ping_role_id)

    async def setup_logs_and_slotm(self, host: discord.Member):
        """
        Set up the logs channel and slot manager for the tournament.

        Args:
            host (discord.Member): The host of the tournament.

        This function sets up the logs channel and slot manager for the tournament. It creates a text channel for the slot manager,
        sets the necessary permissions, and sends the initial slot manager message. It also creates a logs channel for logging
        tournament-related events and sends a message with instructions and information about the tourney-mod role.

        Note: This function assumes that the guild, registration_channel, tourney_mod_role, and logs_channel attributes are already set.

        """
        from cogs.esports.views.tourney.slotm_panel import TourneySlotmPublicPanel

        guild = self.guild
        view = TourneySlotmPublicPanel(self)
        cat = self.registration_channel.category or self.registration_channel.guild

        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            self.guild.me: discord.PermissionOverwrite(manage_channels=True, manage_permissions=True),
        }

        slotm_channel = await cat.create_text_channel(name="tourney-slotmanager", overwrites=overwrites)
        slot_message = await slotm_channel.send(embed=view.initial_embed(), view=view)

        self.slotm_channel_id = slotm_channel.id
        self.slotm_message_id = slot_message.id

        # Setup Logs Channel & Role
        reason = "Created for tourney management."

        if not (tourney_mod_role := self.tourney_mod_role):
            tourney_mod_role = await guild.create_role(name="tourney-mod", color=self.bot.color, reason=reason)

        overwrite = self.registration_channel.overwrites_for(guild.default_role)
        overwrite.update(read_messages=True, send_messages=True, read_message_history=True)
        await self.registration_channel.set_permissions(tourney_mod_role, overwrite=overwrite)

        if (tourney_log_channel := self.logs_channel) is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                tourney_mod_role: discord.PermissionOverwrite(read_messages=True),
            }
            tourney_log_channel = await guild.create_text_channel(
                name="quotient-tourney-logs",
                overwrites=overwrites,
                reason=reason,
                topic="**DO NOT RENAME THIS CHANNEL**",
            )

            note = await tourney_log_channel.send(
                embed=discord.Embed(
                    description=f"If events related to tournament i.e opening registrations or adding roles, "
                    f"etc are triggered, then they will be logged in this channel. "
                    f"Also I have created {tourney_mod_role.mention}, you can give that role to your "
                    f"tourney-moderators. User with {tourney_mod_role.mention} can also send messages in "
                    f"registration channels and they won't be considered as tourney-registration.\n\n"
                    f"`Note`: **Do not rename/delete this channel.**",
                    color=discord.Color(self.bot.color),
                )
            )
            await tourney_log_channel.send(f"{host.mention} **Read This Message 👆**")
            await note.pin()


class TourneyAssignedSlot(BaseDbModel):
    class Meta:
        table = "tourney_assigned_slots"

    id = fields.IntField(primary_key=True, db_index=True)
    num = fields.SmallIntField()
    leader_id = fields.BigIntField(null=True)
    team_name = fields.CharField(max_length=100, null=True)
    members = ArrayField("BIGINT", default=list)
    reg_jump_url = fields.CharField(max_length=300, null=True)
    confirm_msg_jump_url = fields.CharField(max_length=300, null=True)
    cancelled = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    tourney: fields.ForeignKeyRelation[Tourney] = fields.ForeignKeyField("default.Tourney", related_name="assigned_slots")
