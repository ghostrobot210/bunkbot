from src.bunkbot import bunkbot
from src.util.registry import initialize

"""
Primary entry file for the discord bot which
initializes the one and only BunkBot

@author Kevin Yanuk
@license MIT
"""

@bunkbot.event
async def on_ready() -> None:
    await bunkbot.on_init()


if __name__ == "__main__":
    initialize(bunkbot)