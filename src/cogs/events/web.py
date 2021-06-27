from constants import IST
from core import Quotient, Cog
from models import Web, Scrim, Guild, Timer
from datetime import datetime, timedelta

class WebEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    async def deny_creation(self, payload, reason):
        return await Web.filter(id=payload.id).update(estatus=2, response=reason)

    @Cog.listener()
    async def on_scrim_edit_timer_complete(self, payload: Web):
        data = payload.data

        guild = self.bot.get_guild(int(data.get("guild_id")))
        scrim = await Scrim.get_or_none(id=int(data.get("id")))

        if not all((guild, scrim)):
            return

        _dict = {
            "name": data.get("name"),
            "required_mentions": int(data.get("required_mentions")),
            "start_from": int(data.get("start_from")),
            "total_slots": int(data.get("total_slots")),
            "autoslotlist": data.get("autoslotlist"),
            "multiregister": data.get("multiregister"),
            "autodelete_rejects": data.get("autodelete_rejects"),
            "teamname_compulsion": data.get("teamname_compulsion"),
            "no_duplicate_name": data.get("no_duplicate_name"),
        }

        registration_channel_id = int(data.get("registration_channel_id"))
        if not scrim.registration_channel_id == registration_channel_id:
            registration_channel = self.bot.get_channel(int(payload.data.get("registration_channel_id")))

            if not registration_channel:
                return await self.deny_creation(
                    payload, "Quotient cannot see registration channel , Make sure it has appropriate permissions."
                )

            perms = registration_channel.permissions_for(guild.me)
            if not all(
                (
                    perms.send_messages,
                    perms.manage_messages,
                    perms.manage_channels,
                    perms.add_reactions,
                    perms.embed_links,
                )
            ):
                return await self.deny_creation(
                    payload, "Quotient do not have required permissions in the registration channel."
                )

            if registration_channel.id in self.bot.scrim_channels:
                return await self.deny_creation(
                    payload, "The registration channel you selected is already assigned to another scrim."
                )

            _dict["registration_channel_id"] = registration_channel.id

        slotlist_channel_id = int(data.get("slotlist_channel_id"))
        if not scrim.slotlist_channel_id == slotlist_channel_id:
            slotlist_channel = self.bot.get_channel(int(payload.data.get("slotlist_channel_id")))
            if not slotlist_channel:
                return await self.deny_creation(
                    payload, "Quotient cannot see slotlist channel , Can you make sure it has appropriate permissions?"
                )

            perms = slotlist_channel.permissions_for(guild.me)
            if not all(
                (
                    perms.send_messages,
                    perms.manage_messages,
                    perms.manage_channels,
                    perms.add_reactions,
                    perms.embed_links,
                )
            ):
                return await self.deny_creation(
                    payload, "Quotient do not have required permissions in the Slotlist channel."
                )

            _dict["slotlist_channel_id"] = slotlist_channel_id

        role_id = int(data.get("role_id"))
        if not scrim.role_id == role_id:
            role = guild.get_role(int(payload.data.get("role_id")))

            _list = [
                k
                for k, v in dict(role.permissions).items()
                if v is True
                and k in ("manage_channels", "manage_guild", "manage_messages", "manage_roles", "administrator")
            ]
            if _list:
                return await self.deny_creation(
                    payload, "Success role contains some moderation permissions, kindly remove them first."
                )

            _dict["role_id"] = role.id

        ping_role_id = data.get("ping_role_id")
        if ping_role_id and int(ping_role_id) != scrim.ping_role_id:
            _dict["ping_role_id"] = int(ping_role_id)

        _dict["open_role_id"] = int(data.get("open_role_id"))

        epoch = datetime(1970, 1, 1)

        open_time = IST.localize(epoch + timedelta(hours=5, minutes=30, milliseconds=int(data.get("open_time"))))

        _dict["open_time"] = open_time

        if data.get("autoclean_time"):
            autoclean_time = IST.localize(
                epoch + timedelta(hours=5, minutes=30, milliseconds=int(data.get("autoclean_time")))
            )
            if datetime.now(tz=IST) > autoclean_time:
                autoclean_time = autoclean_time + timedelta(hours=24)

            _dict["autoclean_time"] = autoclean_time
            await self.bot.reminders.create_timer(autoclean_time, "autoclean", scrim_id=int(data.get("id")))

        await Web.filter(id=payload.id).update(estatus=1)

        await Scrim.filter(id=int(data.get("id"))).update(**_dict)
        await self.bot.db.execute(
            """UPDATE public."sm.scrims" SET autoclean = $1 , open_days = $2 WHERE id = $3""",
            data.get("autoclean"),
            data.get("open_days"),
            int(data.get("id")),
        )
        await Timer.filter(
            extra={"args": [], "kwargs": {"scrim_id": int(data.get("id"))}}, event__in=("scrim_open", "autoclean")
        ).delete()

        await self.bot.reminders.create_timer(open_time, "scrim_open", scrim_id=int(data.get("id")))

    @Cog.listener()
    async def on_scrim_create_timer_complete(self, payload: Web):
        guild = self.bot.get_guild(int(payload.data.get("guild_id")))
        if not guild:
            return await Web.filter(id=payload.id).delete()

        if not (await Guild.get(guild_id=guild.id)).private_ch:
            return await self.deny_creation(
                payload, "Your server hasn't done Quotient setup yet, kindly run qsetup command once and try again."
            )

        scrim = Scrim(guild_id=guild.id, host_id=int(payload.data.get("host_id")), name=payload.data.get("name"))

        registration_channel = self.bot.get_channel(int(payload.data.get("registration_channel_id")))
        if not registration_channel:
            return await self.deny_creation(
                payload, "Quotient cannot see registration channel , Make sure it has appropriate permissions."
            )

        perms = registration_channel.permissions_for(guild.me)
        if not all(
            (perms.send_messages, perms.manage_messages, perms.manage_channels, perms.add_reactions, perms.embed_links)
        ):
            return await self.deny_creation(
                payload, "Quotient do not have required permissions in the registration channel."
            )

        if registration_channel.id in self.bot.scrim_channels:
            return await self.deny_creation(
                payload, "The registration channel you selected is already assigned to another scrim."
            )

        scrim.registration_channel_id = registration_channel.id

        slotlist_channel = self.bot.get_channel(int(payload.data.get("slotlist_channel_id")))
        if not slotlist_channel:
            return await self.deny_creation(
                payload, "Quotient cannot see slotlist channel , Can you make sure it has appropriate permissions?"
            )

        perms = slotlist_channel.permissions_for(guild.me)
        if not all(
            (perms.send_messages, perms.manage_messages, perms.manage_channels, perms.add_reactions, perms.embed_links)
        ):
            return await self.deny_creation(payload, "Quotient do not have required permissions in the Slotlist channel.")

        scrim.slotlist_channel_id = slotlist_channel.id

        role = guild.get_role(int(payload.data.get("role_id")))

        _list = [
            k
            for k, v in dict(role.permissions).items()
            if v is True and k in ("manage_channels", "manage_guild", "manage_messages", "manage_roles", "administrator")
        ]
        if _list:
            return await self.deny_creation(
                payload, "Success role contains some moderation permissions, kindly remove them first."
            )

        scrim.role_id = role.id

        epoch = datetime(1970, 1, 1)

        scrim.required_mentions = payload.data.get("required_mentions")
        scrim.total_slots = payload.data.get("total_slots")
        scrim.open_time = IST.localize(epoch + timedelta(hours=5, minutes=30, milliseconds=payload.data.get("open_time")))

        await Web.filter(id=payload.id).update(estatus=1)

        await scrim.save()
        await self.bot.reminders.create_timer(scrim.open_time, "scrim_open", scrim_id=scrim.id)

    @Cog.listener()
    async def on_guild_update_timer_complete(self, payload: Web):
        guild = await Guild.get(guild_id=int(payload.data.get("guild_id")))
        self.bot.guild_data[guild.guild_id] = {
            "prefix": guild.prefix,
            "color": guild.embed_color,
            "footer": guild.embed_footer,
        }

        await Web.filter(id=payload.id).update(estatus=1)

    @Cog.listener()
    async def on_scrim_delete_timer_complete(self, payload: Web):
        await Scrim.filter(id=int(payload.data.get("id"))).delete()
        self.bot.scrim_channels.discard(int(payload.data.get("registration_channel_id")))
        await Web.filter(id=payload.id).update(estatus=1)
