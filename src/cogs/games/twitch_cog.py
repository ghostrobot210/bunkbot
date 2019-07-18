import datetime
from urllib.request import HTTPError, URLError, socket
from twitch import TwitchClient
from discord import Embed, Message
from discord.ext import commands
from discord.ext.commands import command
from tinydb import Query
from src.bunkbot import BunkBot
from src.storage.db import database
from src.util.async import AsyncSchedulerHelper
from src.util.helpers import EST, now
from src.util.bunk_exception import BunkException
from src.util.constants import *

TWITCH_URL: str = "https://api.twitch.tv/helix/streams"
TWITCH_ICON: str = "https://vignette.wikia.nocookie.net/fallout/images/4/43/Twitch_icon.png/revision/latest?cb=20180507131302"

"""
Class to handle a twitch stream check
every 60 minutes and allow people to add urls
"""
class TwitchCog:
    def __init__(self, bot: BunkBot):
        self.bot: BunkBot = bot
        self.current_stream_ids = []
        self.msg_stream_list = None
        self.msg_help = None
        self.twitch_client = TwitchClient(client_id=database.get(DB_TWITCH_ID))
        self.init_check = True
        BunkBot.on_bot_initialized += self.wire_stream_listener
        BunkBot.on_msg_received += self.rm_msg


    # wire up the hourly even that will
    # search for twitch streams
    async def wire_stream_listener(self) -> None:
        try:
            # clear out the channel if it
            # is the initial check
            if self.init_check:
                await self.bot.purge_from(self.bot.streams, check=self.rm_unwanted_messages_predicate)

            await self.update_stream_list()
            AsyncSchedulerHelper.add_job(self.update_stream_list, trigger="interval", minutes=60)
        except Exception as e:
            await self.bot.handle_error(e, "wire_stream_listener")


    # list currently followed streams
    @command(pass_context=True, cls=None, help="List currently followed streams", aliases=["update", "refresh"])
    async def streams(self, ctx) -> None:
        await self.bot.send_typing(ctx.message.channel)
        await self.update_stream_list()


    # helper fn to update current stream list - used by
    # the 30 minute interval and !streams or !update command
    async def update_stream_list(self) -> None:
        try:
            this_moment = datetime.datetime.now(EST)

            if 23 >= this_moment.hour >= 16:
                stream_names = []
                stream_statuses = []
                added_bys = []

                all_streams = database.streams.all()

                for s in sorted(all_streams, key=lambda x: x["name"]):
                    stream_names.append(s["name"])
                    added_bys.append(s["added_by"])

                stream_ids = self.twitch_client.users.translate_usernames_to_ids(stream_names)

                stream_count = 1
                for stream in stream_ids:
                    strm = self.twitch_client.streams.get_stream_by_user(stream.id)
                    if strm is not None:
                        stream_statuses.append(strm.channel.url)
                    else:
                        stream_statuses.append("Not streaming")

                    stream_count += 1

                embed = Embed(title="Currently Followed Streams", color=int("19CF3A", 16))
                embed.add_field(name="Stream", value="\n".join(stream_names), inline=True)
                embed.add_field(name="Status", value="\n".join(stream_statuses), inline=True)
                embed.set_thumbnail(url=TWITCH_ICON)
                embed.set_footer(text="type !stream <stream name> to add a stream to the list", icon_url=TWITCH_ICON)

                if not self.msg_stream_list:
                    if self.init_check:
                        self.init_check = False
                        self.msg_stream_list = await self.bot.say_to_channel(self.bot.streams, None, embed)
                    else:
                        self.msg_stream_list = await self.bot.say(embed=embed)
                else:
                    self.msg_stream_list = await self.bot.edit_message(self.msg_stream_list, None, embed=embed)

                h_text = "Type !refresh or !update to refresh the current stream list";
                if not self.msg_help:
                    self.msg_help = await self.bot.say_to_channel(self.bot.streams, h_text)
                else:
                    h_text += " (last updated {0})".format(now())
                    self.msg_help = await self.bot.edit_message(self.msg_help, h_text)
        except Exception as e:
            await self.bot.handle_error(e, "streams")


    # on event emission delete a message
    # that is not a twitch cog command
    async def rm_msg(self, msg: Message) -> None:
        if msg.channel.id == self.bot.streams.id:
            if msg.id != self.msg_stream_list.id and msg.id != self.msg_help.id:
                await self.bot.delete_message(msg)


    # when purging messages from the streaming channel
    # persist the self/streams messages
    def rm_unwanted_messages_predicate(self, message: Message) -> bool:
        if not self.msg_stream_list:
            return True

        if not self.msg_help:
            return True

        return message.id != self.msg_stream_list.id and message.id != self.msg_help.id


    # executable command which will
    # display current weather conditions for
    # a given zip code
    @commands.has_any_role(ROLE_ADMIN)
    @command(pass_context=True, cls=None, help="Add a stream to the database")
    async def stream(self, ctx) -> None:
        try:
            await self.bot.send_typing(ctx.message.channel)
            self.msg_help = await self.bot.edit_message(self.msg_help, "Updating...")

            params = self.bot.get_cmd_params(ctx)
            if len(params) == 0:
                raise BunkException("Enter a stream name")

            param_split = params[0].split("/")
            sname = param_split[len(param_split) - 1]
            stream = database.streams.get(Query().name == sname)

            if stream is not None:
                self.msg_help = await self.bot.edit_message(self.msg_help,
                                                            "Type !refresh or !update to refresh the current stream list")
                raise BunkException("Stream '{0}' has already been added to the database!".format(sname))

            stream_ids = self.twitch_client.users.translate_usernames_to_ids([sname])
            if len(stream_ids) == 0:
                raise BunkException("Cannot find stream '{0}'".format(sname))

            database.streams.insert({"name": sname, "added_by": ctx.message.author.name})
            strm = self.twitch_client.streams.get_stream_by_user(stream_ids[0].id)

            if strm is None and ctx.message.channel.id != self.bot.streams.id:
                await self.bot.say("Stream '{0}' has been added to the database, but is not currently streaming."
                                   .format(sname))
            else:
                if ctx.message.channel.id != self.bot.streams.id:
                    await self.bot.say("Stream '{0}' has been added to the database and is now streaming: {1}"
                                       .format(sname, strm.channel.url))

            await self.update_stream_list()

        except BunkException as be:
            if ctx.message.channel.id != self.bot.streams.id:
                await self.bot.say(be.message)
        except Exception as e:
            await self.bot.handle_error(e, "stream")


    # loop over saved streams in the database
    # and check whether they are streaming
    # TODO - not used
    async def get_streams(self) -> None:
        try:
            now = datetime.datetime.now(EST)
            if 23 >= now.hour >= 10:
                streams = []
                for s in database.streams.all():
                    streams.append(s["name"])

                stream_ids = self.twitch_client.users.translate_usernames_to_ids(streams)

                for stream in stream_ids:
                    strm = self.twitch_client.streams.get_stream_by_user(stream.id)

                    if strm is not None:
                        if stream.id not in self.current_stream_ids:
                            self.current_stream_ids.append(stream.id)
                            ch = strm.channel

                            embed = Embed(title="{0} - streaming {1}".format(ch.display_name, strm.game),
                                          description=ch.status + "\n{0}".format(ch.url),
                                          color=int("392e5c", 16))

                            embed.set_footer(text="type !streams to get followed streams", icon_url=TWITCH_ICON)
                            embed.set_thumbnail(url=ch.logo)

                            await self.bot.say_to_channel(self.bot.general, None, embed)
                    else:
                        if stream.id in self.current_stream_ids:
                            self.current_stream_ids.remove(stream.id)
                            await self.bot.say_to_channel(self.bot.general, "{0} is no longer streaming".format(stream.display_name))
            else:
                self.current_stream_ids = []

        except socket.timeout:
            await self.bot.handle_error("http timeout", "get_streams")
        except (HTTPError, URLError) as uhe:
            await self.bot.handle_error(uhe, "get_streams")
        except Exception as e:
            await self.bot.handle_error(e, "get_streams")


def setup(bot: BunkBot) -> None:
    bot.add_cog(TwitchCog(bot))