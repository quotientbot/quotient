import os

import discord
from asyncpg import Pool
from tortoise import fields

from quotient.models import BaseDbModel
from quotient.models.others.premium import GuildTier


async def create_guild_if_not_exists(pool: Pool, guild_id: int):
    await pool.execute(
        "INSERT INTO guilds (guild_id, prefix, tier) VALUES ($1, $2, $3) ON CONFLICT (guild_id) DO NOTHING",
        guild_id,
        os.getenv("DEFAULT_PREFIX"),
        0,
    )


async def bulk_create_guilds(pool: Pool, guild_ids: list[int]):
    await pool.executemany(
        "INSERT INTO guilds (guild_id, prefix, tier) VALUES ($1, $2, $3) ON CONFLICT (guild_id) DO NOTHING",
        [(guild_id, os.getenv("DEFAULT_PREFIX"), 0) for guild_id in guild_ids],
    )


class Guild(BaseDbModel):
    class Meta:
        table = "guilds"

    guild_id = fields.BigIntField(primary_key=True, db_index=True, generated=False)
    prefix = fields.CharField(default=os.getenv("DEFAULT_PREFIX"), max_length=5)

    tier = fields.IntEnumField(GuildTier, default=GuildTier.FREE)
    upgraded_by = fields.BigIntField(null=True)
    upgraded_until = fields.DatetimeField(null=True)

    @property
    def _guild(self) -> discord.Guild:
        return self.bot.get_guild(self.guild_id)

    @property
    def is_premium(self) -> bool:
        return self.tier != GuildTier.FREE

    async def copy_premium_to_pro(self):
        await self.bot.pro_pool.execute(
            """
            INSERT INTO guilds (guild_id, prefix, tier, upgraded_by, upgraded_until)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (guild_id)
            DO UPDATE SET tier = $3, upgraded_by = $4, upgraded_until = $5""",
            self.guild_id,
            "q!",
            self.tier.value,
            self.upgraded_by,
            self.upgraded_until,
        )
