
CREATE TABLE IF NOT EXISTS smanager.slotlist (
    s_id integer,
    slot_number integer,
    user_id bigint,
    team_name character varying,
    teammates bigint [],
    jump_url text
);
CREATE TABLE IF NOT EXISTS smanager.tag_check (
    guild_id bigint NOT NULL,
    channel_id bigint NOT NULL,
    toggle boolean DEFAULT TRUE,
    PRIMARY KEY (guild_id)
);
CREATE TABLE IF NOT EXISTS smanager.reserved (
    s_id integer,
    guild_id bigint,
    user_id bigint,
    team_name character varying,
    reserved_until timestamp without time zone
);