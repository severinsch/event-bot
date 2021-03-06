from discord.ext.commands import Cog, command
from discord.ext import commands

from lib.bot import COGS, Bot


class Admin(Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("admin")

    @command(name='load')
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, cog):
        """Loads a previously not loaded Cog"""
        if cog not in COGS:
            await ctx.send(f'cog \"{cog}\" not found')
            return

        self.bot.load_extension(f"lib.cogs.{cog}")
        await ctx.message.add_reaction('\U00002705')

    @command(name='unload')
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx, cog):
        """Unloads a previously loaded Cog"""
        if cog not in COGS or cog == "admin":
            await ctx.send(f'cog \"{cog}\" not found or invalid')
            return

        self.bot.unload_extension(f"lib.cogs.{cog}")
        await ctx.message.add_reaction('\U00002705')

    @command(name='reload')
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx, cog):
        """Reloads a previously loaded Cog"""
        if cog not in COGS:
            await ctx.send(f'cog \"{cog}\" not found')
            return
        self.bot.reload_extension(f"lib.cogs.{cog}")
        await ctx.message.add_reaction('\U00002705')


def setup(bot):
    bot.add_cog(Admin(bot))
