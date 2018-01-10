import discord
from discord.ext import commands
import random
import time

class misc:
    """My custom cog that does stuff"""
    def __init__(self, bot):
        self.bot = bot
        self.bank = Bank(bot, "data/economy/bank.json")

    def role_colour():
        #Rand between 0 - 256
        a = random.randrange(0,256)
        b = random.randrange(0,256)
        c = random.randrange(0,256)

        if a != 0 or b != 0 or c != 0:
            choice = random.randrange(1,4)
            if choice === 1:
                a = 0
            if choice === 2:
                b = 0
            if choice === 3:
                c = 0

        return a, b, c

    def change_colour(r, g, b):
        picked_role = bot.role("400618311861272577")
        bot.edit_role(role=picked_role, colour=bot.colour(r, g, b))

    def colour_loop():
        while true:
            change_colour(role_colour())
            time.sleep(5)

    colour_loop()
        
def setup(bot):
    bot.add_cog(Counter(bot))
