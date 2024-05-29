import logging

from asyncpg import Pool
from models import BaseDbModel
from tortoise import fields


async def create_user_if_not_exists(pool: Pool, user_id: int):
    await pool.execute(
        "INSERT INTO users (user_id, email_id, phone_number) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
        user_id,
        None,
        None,
    )


class User(BaseDbModel):
    class Meta:
        table = "users"

    user_id = fields.BigIntField(primary_key=True, db_index=True)
    email_id = fields.CharField(max_length=50, null=True)
    phone_number = fields.CharField(max_length=15, null=True)
