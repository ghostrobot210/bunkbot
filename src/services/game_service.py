from discord import Game, Member

from .database_service import DatabaseService
from .channel_service import ChannelService
from .user_service import UserService
from ..bunkbot import BunkBot
from ..models.service import Service
from ..models.bunk_user import BunkUser

"""
Service specifically designed to deal with things like
setting BunkBot's played game, twitch streams, etc.
"""
class GameService(Service):
    def __init__(self, bot: BunkBot, database: DatabaseService, channels: ChannelService, users: UserService):
        super().__init__(bot, database)
        self.channels: ChannelService = channels
        self.users: UserService = users
        self.bot.on_initialized += self.set_game
        self.bot.on_initialized += self.check_streams


    # every so often, set the bot status - if the bot
    # has decided to go "away" or do something else, do
    # not wire any game 
    async def set_game(self) -> None:
        pass


    # when a user has started to play a game, check the known
    # games and store it into the database if it does not currently exist
    async def get_game(self, game: Game) -> None:
        pass


    # do an initial check of current streams and update
    # the list in the stream channel
    async def check_streams(self) -> None:
        # TODO - currently disabled until the twitch API is fixed
        pass