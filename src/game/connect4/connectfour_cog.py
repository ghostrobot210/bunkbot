from typing import List
from discord import Message, TextChannel
from discord.ext.commands import command, Context, Cog

from .c4_game import ConnectFourGame
from ..game_service import GameService
from ...bunkbot import BunkBot
from ...core.bunk_user import BunkUser
from ...core.registry import GAME_SERVICE
from ...channel.channel_service import ChannelService
from ...user.user_service import UserService


"""
Cog that will setup connect four games
"""
class ConnectFourCog(Cog):
    def __init__(self, bot: BunkBot, game_service: GameService):
        self.game_service: GameService = game_service
        self.games: List[ConnectFourGame] = []
        bot.on_user_message += self.get_answer


    @command(help="Create a game of connect four!", aliases=["c4"])
    async def connectfour(self, ctx: Context) -> None:
        await ctx.message.delete()
        user: BunkUser = self.game_service.users.get_by_id(ctx.message.author.id)
        channel: TextChannel = await self.game_service.create_game_channel("connect4", user)

        if channel is not None:
            print("TODO - check existing game")
            game = ConnectFourGame(user, channel)
            self.games.append(game)
            await game.start()


    async def get_answer(self, message: Message) -> None:
        if not message.author.bot:
            if message.channel.name == "connect4-fugwenna":
                user: BunkUser = self.game_service.users.get_by_id(message.author.id)
                await message.delete()
                await self.games[0].update(message, user)
    

def setup(bot: BunkBot) -> None:
    bot.add_cog(ConnectFourCog(bot, GAME_SERVICE))
