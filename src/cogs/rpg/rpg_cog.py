"""
RPG commands based on a user level
"""
from discord import Embed
from discord.ext import commands
from src.bunkbot import BunkBot
from src.storage.db import database
from .rpg import rpg

class BunkRPG:
    def __init__(self, bot: BunkBot):
        self.bot = bot
        rpg.on_user_level += self.ding


    # DING - user has leveled up
    # inform them and update their server permissions
    async def ding(self, member, value):
        # TODO - send to general when this is stable
        if member.name != "fugwenna":
            await self.bot.say_to_channel(self.bot.general, ":bell: DING! {0.mention} has advanced to level {1}!"
                                      .format(member, value))


    # allow users to print
    # out their current level
    @commands.command(pass_context=True, cls=None, help="Print your current level", aliases=["rank"])
    async def level(self, ctx):
        await self.bot.send_typing(ctx)

        user = database.get_user(ctx.message.author)

        #todo embed with pct
        await self.bot.say("You are currently level {0}".format(user["level"]))



def setup(bot) -> None:
    bot.add_cog(BunkRPG(bot))