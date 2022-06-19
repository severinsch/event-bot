from discord import Role, RawScheduledEventSubscription, ScheduledEvent
from discord.ext.commands import Cog, group, Context, has_permissions
from lib.bot import Bot
from lib.db import db
from lib.utils import utils
from lib.utils.utils import get_info_embed, parse_command_args, get_events_info, delete_event, \
    handle_scheduled_event_user_change


class EventCog(Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("event")

    @group(invoke_without_command=True)
    async def event(self, ctx: Context):
        embed = get_info_embed(ctx.prefix, command='event')
        await ctx.send(embed=embed)

    @event.command()
    @has_permissions(administrator=True)
    async def add(self, ctx: Context, *, event: str):
        """!event add name;description;start date;start time;end date; end time; place"""
        try:
            name, description, place, start, end, role_name = parse_command_args(event)
        except ValueError as e:
            await ctx.send(str(e))
            return
        role: Role = await ctx.guild.create_role(name=role_name, mentionable=True)
        event = await ctx.guild.create_scheduled_event(name=name,
                                                       description=description,
                                                       start_time=start,
                                                       end_time=end,
                                                       location=place)

        db.execute(
            'INSERT INTO '
            'events (guild_id, discord_event_id, role_id) '
            'VALUES (?,?,?)', ctx.guild.id, event.id, role.id)

    @event.command()
    async def list(self, ctx: Context):
        events = await get_events_info(ctx.guild)
        if not events:
            await ctx.send('No upcoming events :(')
            return
        await utils.send_paginated(ctx, start="```", end="```", content='\n'.join(events))

    @Cog.listener()
    async def on_scheduled_event_create(self, event: ScheduledEvent):
        role_name = f'event-{"-".join(event.name.lower().split(" "))}'
        role: Role = await event.guild.create_role(name=role_name, mentionable=True)
        db.execute(
            'INSERT INTO '
            'events (guild_id, discord_event_id, role_id) '
            'VALUES (?,?,?)', event.guild.id, event.id, role.id)

    @Cog.listener()
    async def on_scheduled_event_delete(self, event: ScheduledEvent):
        await delete_event(bot=self.bot, discord_event_id=event.id)

    @Cog.listener()
    async def on_raw_scheduled_event_user_add(self, payload: RawScheduledEventSubscription):
        await handle_scheduled_event_user_change(payload)

    @Cog.listener()
    async def on_raw_scheduled_event_user_remove(self, payload: RawScheduledEventSubscription):
        await handle_scheduled_event_user_change(payload)


def setup(bot):
    bot.add_cog(EventCog(bot))
