import os
import sys

from asyncio import sleep
from discord.ext.commands import Bot as BotBase
from discord.ext import commands, tasks
from discord import Intents

from lib.bot.config import Config
from lib.db import db

COGS = [path[:-3] for path in os.listdir('./lib/cogs') if path[-3:] == '.py']


class Ready:
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f"{cog} cog ready")

    def all_ready(self):
        return all([getattr(self, cog) for cog in COGS])


class Bot(BotBase):
    def __init__(self):
        config_file = "config.toml"
        if len(sys.argv) > 1:
            config_file = sys.argv[1]
        self.config = Config(config_file)
        self.ready = False
        self.cogs_ready = Ready()
        self.guild = None
        super().__init__(
            command_prefix=self.config.command_prefix,
            owner_id=self.config.owner_id,
            intents=Intents.all(),
            description=self.config.desc,
            case_insensitive=True
        )

    # loading cogs
    def setup(self):
        for cog in COGS:
            self.load_extension(f"lib.cogs.{cog}")
            print(f"{cog} cog loaded")
        print("setup complete")

    def run(self):
        self.setup()
        print("running bot..")
        super().run(self.config.discord_token, reconnect=True)

    async def on_connect(self):
        print("bot running")

    async def on_disconnect(self):
        print("bot disconnected")

    async def on_command_error(self, ctx, exc):
        if isinstance(exc, commands.errors.CommandNotFound):
            print('command not found')
        elif isinstance(exc, commands.errors.CommandOnCooldown):
            await ctx.send("not so fast")
        elif isinstance(exc, commands.errors.BotMissingPermissions):
            await ctx.send("Bot not powerful enough :(")
        else:
            print(f'other exception {exc}')

    async def on_ready(self):
        if not self.ready:
            self.guild = self.get_guild(self.config.guild_id)
            # wait for cogs to be ready
            while not self.cogs_ready.all_ready():
                await sleep(0.5)
            self.ready = True
            self.commit.start()
            print("bot ready")
        else:
            print("bot reconnected")

    @tasks.loop(seconds=30)
    async def commit(self):
        print(f'commit loop')
        db.commit()


bot = Bot()
