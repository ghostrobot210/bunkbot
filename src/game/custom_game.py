from discord import TextChannel, Message

"""
Base model for custom games with
some basic methods built in
"""
class CustomGame:
    def __init__(self, channel: TextChannel):
        self.channel: TextChannel = channel
        self.set_defaults()


    def set_defaults(self) -> None:
        self.is_cancelled: bool = False


    async def is_cancel(self, msg: Message) -> None:
        l_content: str = msg.content.lower()
        if l_content == "cancel":
            self.is_cancelled = True
            await self.cancel_game()


    def get_content(self, msg: Message) -> None:
        return msg.content.lower()

        
    async def cancel_game(self) -> None:
        await self.channel.delete()