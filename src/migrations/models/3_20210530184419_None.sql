-- upgrade --
CREATE TABLE IF NOT EXISTS "sm.assigned_slots" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "team_name" TEXT,
    "members" BIGINT[] NOT NULL,
    "num" INT NOT NULL,
    "jump_url" TEXT
);
CREATE TABLE IF NOT EXISTS "autoevents" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "guild_id" BIGINT NOT NULL,
    "type" VARCHAR(30) NOT NULL,
    "channel_id" BIGINT NOT NULL,
    "webhook" VARCHAR(200) NOT NULL,
    "toggle" BOOL NOT NULL  DEFAULT True,
    "interval" INT NOT NULL  DEFAULT 30,
    "send_time" TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_autoevents_webhook_1b2e4f" ON "autoevents" ("webhook");
CREATE INDEX IF NOT EXISTS "idx_autoevents_send_ti_f8a4b1" ON "autoevents" ("send_time");
COMMENT ON COLUMN "autoevents"."type" IS 'meme: meme\nfact: fact\nquote: quote\njoke: joke\nnsfw: nsfw\nadvice: advice\npoem: poem';
CREATE TABLE IF NOT EXISTS "autoroles" (
    "guild_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "humans" BIGINT[] NOT NULL,
    "bots" BIGINT[] NOT NULL
);
CREATE TABLE IF NOT EXISTS "sm.banned_teams" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "team_name" TEXT,
    "members" BIGINT[] NOT NULL,
    "expires" TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS "cmd_stats" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "guild_id" BIGINT NOT NULL,
    "user_id" BIGINT NOT NULL,
    "cmd" TEXT NOT NULL,
    "uses" INT NOT NULL  DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "guild_data" (
    "guild_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "prefix" VARCHAR(5) NOT NULL  DEFAULT 'q',
    "embed_color" INT   DEFAULT 65459,
    "embed_footer" TEXT NOT NULL,
    "bot_master" BIGINT[] NOT NULL,
    "muted_members" BIGINT[] NOT NULL,
    "tag_enabled_for_everyone" BOOL NOT NULL  DEFAULT True,
    "emoji_stealer_channel" BIGINT,
    "emoji_stealer_message" BIGINT,
    "is_premium" BOOL NOT NULL  DEFAULT False,
    "made_premium_by" BIGINT,
    "premium_end_time" TIMESTAMPTZ,
    "premium_notified" BOOL NOT NULL  DEFAULT False,
    "public_profile" BOOL NOT NULL  DEFAULT True,
    "private_channel" BIGINT,
    "private_webhook" TEXT,
    "disabled_channels" BIGINT[] NOT NULL,
    "disabled_commands" TEXT[] NOT NULL,
    "disabled_users" BIGINT[] NOT NULL,
    "censored" TEXT[] NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_guild_data_bot_mas_45bfc0" ON "guild_data" ("bot_master");
CREATE INDEX IF NOT EXISTS "idx_guild_data_emoji_s_61a058" ON "guild_data" ("emoji_stealer_channel");
CREATE INDEX IF NOT EXISTS "idx_guild_data_emoji_s_d436bd" ON "guild_data" ("emoji_stealer_message");
CREATE INDEX IF NOT EXISTS "idx_guild_data_private_3f87e0" ON "guild_data" ("private_channel");
CREATE INDEX IF NOT EXISTS "idx_guild_data_disable_c75dc8" ON "guild_data" ("disabled_channels");
CREATE INDEX IF NOT EXISTS "idx_guild_data_disable_09fddc" ON "guild_data" ("disabled_users");
CREATE INDEX IF NOT EXISTS "idx_guild_data_censore_bac66b" ON "guild_data" ("censored");
CREATE TABLE IF NOT EXISTS "lockdown" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "guild_id" BIGINT NOT NULL,
    "type" VARCHAR(20) NOT NULL,
    "role_id" BIGINT,
    "channel_id" BIGINT,
    "channel_ids" BIGINT[] NOT NULL,
    "expire_time" TIMESTAMPTZ,
    "author_id" BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_lockdown_guild_i_46683b" ON "lockdown" ("guild_id");
CREATE INDEX IF NOT EXISTS "idx_lockdown_channel_6bf8cc" ON "lockdown" ("channel_ids");
COMMENT ON COLUMN "lockdown"."type" IS 'channel: channel\nguild: guild\ncategory: category\nmaintenance: maintenance';
CREATE TABLE IF NOT EXISTS "logging" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "guild_id" BIGINT NOT NULL,
    "channel_id" BIGINT NOT NULL,
    "color" INT NOT NULL  DEFAULT 3092790,
    "toggle" BOOL NOT NULL  DEFAULT True,
    "ignore_bots" BOOL NOT NULL  DEFAULT False,
    "type" VARCHAR(12) NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_logging_guild_i_a6e6ac" ON "logging" ("guild_id");
CREATE INDEX IF NOT EXISTS "idx_logging_type_2368a3" ON "logging" ("type");
COMMENT ON COLUMN "logging"."type" IS 'msg: msg\njoin: join\nleave: leave\naction: action\nserver: server\nchannel: channel\nrole: role\nmember: member\nvoice: voice\nreaction: reaction\nmod: mod\ncmd: cmd\ninvite: invite\nping: ping';
CREATE TABLE IF NOT EXISTS "premium_logs" (
    "order_id" VARCHAR(50) NOT NULL  PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "payment_id" VARCHAR(50),
    "payment_time" TIMESTAMPTZ,
    "plan_1" INT   DEFAULT 0,
    "plan_2" INT   DEFAULT 0,
    "plan_3" INT   DEFAULT 0,
    "amount" INT   DEFAULT 0,
    "token" TEXT,
    "is_done" BOOL   DEFAULT False,
    "order_time" TIMESTAMPTZ,
    "username" VARCHAR(200),
    "email" VARCHAR(200),
    "is_notified" BOOL   DEFAULT False
);
CREATE TABLE IF NOT EXISTS "redeem_codes" (
    "user_id" BIGINT NOT NULL,
    "code" VARCHAR(50) NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "expire_time" TIMESTAMPTZ NOT NULL,
    "is_used" BOOL NOT NULL  DEFAULT False,
    "used_by" BIGINT,
    "used_at" TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS "sm.reserved_slots" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "team_name" TEXT,
    "members" BIGINT[] NOT NULL,
    "expires" TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS "sm.scrims" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "guild_id" BIGINT NOT NULL,
    "name" TEXT NOT NULL,
    "registration_channel_id" BIGINT NOT NULL,
    "slotlist_channel_id" BIGINT NOT NULL,
    "slotlist_message_id" BIGINT,
    "role_id" BIGINT,
    "required_mentions" INT NOT NULL,
    "start_from" INT NOT NULL  DEFAULT 1,
    "available_slots" INT[] NOT NULL,
    "total_slots" INT NOT NULL,
    "host_id" BIGINT NOT NULL,
    "open_time" TIMESTAMPTZ NOT NULL,
    "opened_at" TIMESTAMPTZ,
    "closed_at" TIMESTAMPTZ,
    "autoclean" BOOL NOT NULL  DEFAULT False,
    "autoslotlist" BOOL NOT NULL  DEFAULT True,
    "ping_role_id" BIGINT,
    "multiregister" BOOL NOT NULL  DEFAULT False,
    "stoggle" BOOL NOT NULL  DEFAULT True,
    "open_role_id" BIGINT,
    "open_days" VARCHAR(9)[] NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_sm.scrims_registr_83e2b4" ON "sm.scrims" ("registration_channel_id");
CREATE TABLE IF NOT EXISTS "snipes" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "author_id" BIGINT NOT NULL,
    "channel_id" BIGINT NOT NULL,
    "content" TEXT NOT NULL,
    "delete_time" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "nsfw" BOOL NOT NULL  DEFAULT False
);
CREATE TABLE IF NOT EXISTS "tm.register" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "num" INT NOT NULL,
    "team_name" TEXT NOT NULL,
    "leader_id" BIGINT NOT NULL,
    "members" BIGINT[] NOT NULL,
    "jump_url" TEXT
);
CREATE TABLE IF NOT EXISTS "tags" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "guild_id" BIGINT NOT NULL,
    "name" VARCHAR(100) NOT NULL,
    "content" TEXT NOT NULL,
    "is_embed" BOOL NOT NULL  DEFAULT False,
    "is_nsfw" BOOL NOT NULL  DEFAULT False,
    "owner_id" BIGINT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "usage" INT NOT NULL  DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "tagcheck" (
    "guild_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "channel_id" BIGINT NOT NULL,
    "required_mentions" INT NOT NULL  DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "timer" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "expires" TIMESTAMPTZ NOT NULL,
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "event" TEXT NOT NULL,
    "extra" JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_timer_expires_ad551b" ON "timer" ("expires");
CREATE TABLE IF NOT EXISTS "tm.tourney" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "guild_id" BIGINT NOT NULL,
    "name" VARCHAR(200) NOT NULL  DEFAULT 'Quotient-Tourney',
    "registration_channel_id" BIGINT NOT NULL,
    "confirm_channel_id" BIGINT NOT NULL,
    "role_id" BIGINT NOT NULL,
    "required_mentions" INT NOT NULL,
    "total_slots" INT NOT NULL,
    "banned_users" BIGINT[] NOT NULL,
    "host_id" BIGINT NOT NULL,
    "multiregister" BOOL NOT NULL  DEFAULT False,
    "started_at" TIMESTAMPTZ,
    "closed_at" TIMESTAMPTZ,
    "open_role_id" BIGINT
);
CREATE INDEX IF NOT EXISTS "idx_tm.tourney_registr_beafa1" ON "tm.tourney" ("registration_channel_id");
CREATE TABLE IF NOT EXISTS "user_data" (
    "user_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "is_premium" BOOL NOT NULL  DEFAULT False,
    "premium_expire_time" TIMESTAMPTZ,
    "made_premium" BIGINT[] NOT NULL,
    "premiums" INT NOT NULL  DEFAULT 0,
    "premium_notified" BOOL NOT NULL  DEFAULT False,
    "public_profile" BOOL NOT NULL  DEFAULT True
);
CREATE INDEX IF NOT EXISTS "idx_user_data_is_prem_fcd413" ON "user_data" ("is_premium");
CREATE TABLE IF NOT EXISTS "votes" (
    "user_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "is_voter" BOOL NOT NULL  DEFAULT False,
    "expire_time" TIMESTAMPTZ,
    "reminder" BOOL NOT NULL  DEFAULT False,
    "notified" BOOL NOT NULL  DEFAULT False,
    "public_profile" BOOL NOT NULL  DEFAULT True,
    "total_votes" INT NOT NULL  DEFAULT 0
);
CREATE INDEX IF NOT EXISTS "idx_votes_is_vote_ac3281" ON "votes" ("is_voter");
CREATE INDEX IF NOT EXISTS "idx_votes_notifie_5a2e62" ON "votes" ("notified");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "sm.scrims_sm.banned_teams" (
    "sm.scrims_id" BIGINT NOT NULL REFERENCES "sm.scrims" ("id") ON DELETE CASCADE,
    "bannedteam_id" INT NOT NULL REFERENCES "sm.banned_teams" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "sm.scrims_sm.assigned_slots" (
    "sm.scrims_id" BIGINT NOT NULL REFERENCES "sm.scrims" ("id") ON DELETE CASCADE,
    "assignedslot_id" INT NOT NULL REFERENCES "sm.assigned_slots" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "sm.scrims_sm.reserved_slots" (
    "sm.scrims_id" BIGINT NOT NULL REFERENCES "sm.scrims" ("id") ON DELETE CASCADE,
    "reservedslot_id" INT NOT NULL REFERENCES "sm.reserved_slots" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "tm.tourney_tm.register" (
    "tm.tourney_id" BIGINT NOT NULL REFERENCES "tm.tourney" ("id") ON DELETE CASCADE,
    "tmslot_id" BIGINT NOT NULL REFERENCES "tm.register" ("id") ON DELETE CASCADE
);
