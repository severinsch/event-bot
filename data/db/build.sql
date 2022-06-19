CREATE TABLE IF NOT EXISTS events (
    id integer PRIMARY KEY,
    guild_id integer NOT NULL,
    discord_event_id integer NOT NULL,
    role_id integer NOT NULL
);
