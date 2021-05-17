-- upgrade --
CREATE TABLE IF NOT EXISTS "sm.assigned_slots" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "team_name" TEXT NOT NULL,
    "members" bigint[] NOT NULL,
    "num" INT NOT NULL,
    "jump_url" TEXT
);
CREATE TABLE IF NOT EXISTS "sm.reserved_slots" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "team_name" TEXT NOT NULL,
    "members" bigint[] NOT NULL,
    "expires" TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS "sm.scrims" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "guild_id" BIGINT NOT NULL,
    "name" TEXT NOT NULL,
    "registration_channel_id" BIGINT NOT NULL,
    "slotlist_channel_id" BIGINT NOT NULL,
    "slotlist_sent" BOOL NOT NULL  DEFAULT False,
    "slotlist_message_id" BIGINT,
    "role_id" BIGINT,
    "required_mentions" INT NOT NULL,
    "total_slots" INT NOT NULL,
    "host_id" BIGINT NOT NULL,
    "banned_users_ids" bigint[] NOT NULL,
    "open_time" TIMESTAMPTZ NOT NULL,
    "opened_at" TIMESTAMPTZ,
    "closed_at" TIMESTAMPTZ,
    "autoclean" BOOL NOT NULL  DEFAULT False,
    "autoslotlist" BOOL NOT NULL  DEFAULT True,
    "ping_role_id" BIGINT,
    "stoggle" BOOL NOT NULL  DEFAULT True,
    "open_role_id" BIGINT,
    "open_days" varchar[] NOT NULL
);
CREATE TABLE IF NOT EXISTS "timer" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "expires" TIMESTAMPTZ NOT NULL,
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "event" TEXT NOT NULL,
    "extra" JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_timer_expires_ad551b" ON "timer" ("expires");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "sm.scrims_sm.reserved_slots" (
    "sm.scrims_id" BIGINT NOT NULL REFERENCES "sm.scrims" ("id") ON DELETE CASCADE,
    "reservedslot_id" INT NOT NULL REFERENCES "sm.reserved_slots" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "sm.scrims_sm.assigned_slots" (
    "sm.scrims_id" BIGINT NOT NULL REFERENCES "sm.scrims" ("id") ON DELETE CASCADE,
    "assignedslot_id" INT NOT NULL REFERENCES "sm.assigned_slots" ("id") ON DELETE CASCADE
);
