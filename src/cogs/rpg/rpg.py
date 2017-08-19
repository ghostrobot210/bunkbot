"""
Base RPG class used for leveling users
"""
import time
from discord import Member
from src.storage.db import database
from src.util.event_hook import EventHook


# hard cap the message
# processing to a discrete value
# to prevent channel spamming
# todo - database
XP_CONST = 5
UPDATE_CAP = 60
TIMER_MINUTES = 1


class RPG:
    def __init__(self):
        self.config = {}
        self.on_user_level_up = EventHook()


    # sync a users level with the
    # config if they log on or off
    async def sync_user_xp(self, member: Member) -> None:
        new_user = None

        try:
            user = self.config[member.name]
            new_user = database.update_user_xp(member, user["value"])
        except:
            pass
        finally:
            if new_user is None:
                new_user = database.get_user(member)

            if new_user is not None:
                if str(member.status) == "online" and self.level_up(new_user["xp"], new_user["level"] + 1):
                    database.update_user_level(member)

                    if str(member.status) == "online":
                        leveled_user = database.update_user_level(member)
                        await self.on_user_level_up.fire(member, leveled_user["level"])


    # every time a user sends a message
    # process it for "leveling" logic
    async def update_user_xp(self, member: Member, value: float, duel: bool = False) -> None:
        try:
            user = self.config[member.name]
        except:
            self.config[member.name] = {"value": value, "last_update": time.time()}
            user = self.config[member.name]

        diff = time.time() - user["last_update"]

        if duel or diff > 0:
            min_diff = diff / 60

            # continue to increase the message
            # count until the user has reached a cap
            # during an n minute window
            if not duel and min_diff <= TIMER_MINUTES:
                if user["value"] < UPDATE_CAP:
                    user["value"] += value

            # the window is up, therefore
            # increase the user level percentage and
            # check if they have leveled up
            else:
                new_user = database.update_user_xp(member, user["value"])

                if self.level_up(new_user["xp"], new_user["level"] + 1):
                    leveled_user = database.update_user_level(member)
                    await self.on_user_level_up.fire(member, leveled_user["level"])

                user["last_update"] = time.time()
                user["value"] = value


    # calculate the required xp for a given level
    @staticmethod
    def calc_req_xp(level: int) -> float:
        return (XP_CONST * level * level) - (XP_CONST * level) + round(level / 2, 2)


    # calculate the xp required
    # to advance to the next level
    def level_up(self, xp: float, level: int) -> bool:
        return xp >= self.calc_req_xp(level)

rpg = RPG()