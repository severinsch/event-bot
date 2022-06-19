import discord

from datetime import datetime, timedelta
from discord import Embed, RawScheduledEventSubscription, Guild, ScheduledEvent

from lib.bot import Bot
from lib.db import db


async def handle_scheduled_event_user_change(payload: RawScheduledEventSubscription):
    user_id = payload.user_id
    event_id = payload.event_id
    guild: Guild = payload.guild
    member = await guild.fetch_member(user_id)
    role_id = db.field(f'SELECT role_id FROM events WHERE discord_event_id = ?', event_id)
    if not role_id:
        return
    role = await guild._fetch_role(role_id)
    print(f'{role=}, {member=}')
    if payload.event_type == 'USER_ADD' and role:
        await member.add_roles(role, atomic=True)
    elif role:
        await member.remove_roles(role, atomic=True)


def print_event(event: ScheduledEvent) -> str:
    start = f'from {event.start_time.strftime("%H.%M %d.%m.%y")}'
    end = '' if not event.end_time else ' to {event.end_time.strftime("%H.%M %d.%m.%y")}'
    return f'{event.name}: {event.description}, {start}{end} at {event.location}'


async def get_events_info(guild: Guild) -> list[str]:
    records = db.records('SELECT * FROM events WHERE guild_id = ?', guild.id)
    events: list[ScheduledEvent] = []
    for _, _, discord_event_id, _ in records:
        event = await guild.fetch_scheduled_event(discord_event_id)
        events.append(event)
    events.sort(key=lambda e: e.start_time)
    return [print_event(e) for e in events]


async def delete_event(bot: Bot, discord_event_id: int):
    query = f'SELECT * FROM events WHERE discord_event_id = ?'
    record = db.record(query, discord_event_id)
    if not record:
        return None

    event_id, guild_id, sched_event_id, role_id = record
    guild = await bot.fetch_guild(guild_id)

    roles = [r for r in guild.roles if r.id == role_id]
    if roles:
        await roles[0].delete()

    db.execute('DELETE FROM events WHERE id = ?', event_id)


def get_info_embed(prefix: str, command: str) -> Embed:
    embed = Embed(title='Events')
    embed.add_field(name='Available commands', value='add & list')
    embed.add_field(
        name='Add Usage',
        value=f'{prefix}{command} add name;desc;start date;start time;end date;end time;place',
        inline=False)
    embed.add_field(name='Formats', value='name, desc, place: any text\n dates: YYYY-MM-DD\n times: HH:MM',
                    inline=False)
    start = datetime.now() + timedelta(minutes=30)
    end = start + timedelta(hours=2)
    example = f'{prefix}{command} add Essen;Essen gehen mit der Gang;' \
              f'{start.strftime("%Y-%m-%d;%H:%M;")}{end.strftime("%Y-%m-%d;%H:%M;")}tolles Restaurant'
    embed.add_field(name='Example', value=example)
    return embed


def parse_command_args(arg: str) -> tuple[str, str, str, datetime, datetime, str]:
    args = arg.split(';')
    if len(args) != 7:
        raise ValueError('Invalid number of arguments')
    name: str = args[0]
    description: str = args[1]
    place = args[6]
    try:
        start = datetime.strptime(args[2] + ';' + args[3], '%Y-%m-%d;%H:%M')
        end = datetime.strptime(args[4] + ';' + args[5], '%Y-%m-%d;%H:%M')
    except ValueError:
        raise ValueError("Couldn't parse date")
    role_name = f'event-{"-".join(name.lower().split(" "))}'
    return name, description, place, start, end, role_name


async def send_paginated(ctx, limit=2000, start="", end="", *, content):
    content = discord.utils.escape_mentions(content)
    content = content.replace('`', '`\u200b')
    if len(content) + len(start) + len(end) < limit:
        await ctx.send(start + content + end)
        return
    chunk_size = limit - len(start) - len(end)
    chunks = [start + content[i:i + chunk_size] + end for i in range(0, len(content), chunk_size)]
    for chunk in chunks:
        await ctx.send(chunk)
