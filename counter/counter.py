import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO, fileIO
from collections import namedtuple, defaultdict
from datetime import datetime
from random import randint
from copy import deepcopy
from .utils import checks
from __main__ import send_cmd_help
import os
import time
import logging
from .economy import Bank, BankError, AccountAlreadyExists, NoAccount, InsufficientBalance, SameSenderAndReceiver

class Counter:
    """My custom cog that does stuff"""
    def __init__(self, bot):
        self.bot = bot
        self.bank = Bank(bot, "data/economy/bank.json")
        

    @commands.command(pass_context=True, no_pm=True)
    async def boop(self, ctx, user : discord.Member=None):
        """Boop!"""
        if user != None:
            author = ctx.message.author
            if user != author:
                await self.bot.say("Boop! /) " + user.mention)
            else:
                await self.bot.say("Boop! /) " + user.mention + "    \n\n*ponk*")
        else:
            await self.bot.say("That does not appear to be something I can boop.")

    @commands.command(pass_context=True, no_pm=True)
    async def unflip(self, ctx, user : discord.Member=None):
        """Now with the ability to unflip!"""
        if user != None:
            author = ctx.message.author
            if user != author:
                await self.bot.say(user.mention + " ノ( ゜-゜ノ)")
            else:
                await self.bot.say(user.mention + " ノ( ゜-゜ノ)    \n\n`It's okay - you look better this way`")
        else:
            await self.bot.say("Really? You want me to unflip *that*?")

    @commands.command()
    async def pong(self, user : discord.Member=None):
        """You've seen ping, now get ready for pong!"""
        await self.bot.say("`Ping!`")

    @commands.command(pass_context=True, no_pm=True)
    async def ship(self, ctx, user_1 : discord.Member=None, user_2 : discord.Member=None):
        "Ship yourself, someone else, or two random people"

        msg = " :heart: "
        extra = ""
        member_list = list()
        author = ctx.message.author
        server = ctx.message.server
        
        if user_1 == None:
            for member in server.members:
                if member.id != author.id:
                    member_list.append(member)
            user_1 = member_list[randint(0, len(member_list)-1)]
        
        if user_2 == None:
            for member in server.members:
                if member.id != author.id:
                    member_list.append(member)
            user_2 = member_list[randint(0, len(member_list)-1)]
            
        if user_1 == self.bot.user and user_2 == self.bot.user:
            extra = "\nOh, how funny. I've never seen that response before, imbecile." 
        elif user_1 == self.bot.user or user_2 == self.bot.user:
            extra = "\nYou're not even worth the cheapest drink I bought today in this pub."
        elif user_1 == self.bot.user and user_1 == author:
            extra = "\nI'm flattered, really, but all I would do is merge your DNA into my programming, thus permanently erasing you from this world. Besides, you aren't my type."
        else:
            if user_1 == author and user_2 == author:
                extra = "\n\n`I wonder how desperate you can get.`"
            elif user_1 == author or user_2 == author:
                extra = "\n\n`You know, there's pathetic, and then there's you.`"
        await self.bot.say(user_1.mention + msg + user_2.mention + extra)

    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx, game=None):
        "Finds users playing a particular game"
        
        member_list = list()
        number = 0
        server = ctx.message.server

        for member in server.members:
            if member.game != None:
                if str(member.game).lower() == str(game).lower():
                    member_list.append(member.name)
                    number += 1
        
        if number > 0:        
            await self.bot.say("```{} users playing {}\n{}```".format(number, game, "\n".join(member_list)))
        else:
            await self.bot.say("```I either can't find {}, or you are a master of Engrish.```".format(game))

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def updateboard(self, ctx):
        """Updates usernames"""
        bank_list = self.bank.get_server_accounts(ctx.message.server)
        
        for account in bank_list:
            if account.member != None:
                user = discord.utils.get(ctx.message.server.members, id=account.member.id)
                if user != None:
                    self.bank.accounts[ctx.message.server.id][account.member.id]["name"] = user.name
                    self.bank._save_bank()
            
        await self.bot.say("Updated all registered bank names!\n```It's recommended you reload modules tha rely on accounts```")

    @commands.group(pass_context=True)
    async def top(self, ctx):
        """Top posters"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

    @top.command(pass_context=True, no_pm=True, name="update")
    @checks.admin_or_permissions(administrator=True)
    async def top_update(self, ctx):
        "Get the highest posters"
        ranks = dataIO.load_json("data/counter/ranks.json")
        ranks[ctx.message.server.id] = {}
        await self.bot.say("Running post leaderboard update.")
        for channel in ctx.message.server.channels:
            number = 0
            async for message in self.bot.logs_from(channel, limit=100):
                number = number + 1
                if self.bot.user not in message.mentions and message.author.bot != True:
                    if len(message.content.split(" ")) >= 4 and len(message.content) >= 8 and not message.content.startswith("!"):
                        try:
                            ranks[ctx.message.server.id][message.author.id]["posts"] += 1
                        except KeyError:
                            ranks[ctx.message.server.id][message.author.id] = {}
                            ranks[ctx.message.server.id][message.author.id]["posts"] = 1
                            ranks[ctx.message.server.id][message.author.id]["username"] = message.author.name
                last = message
                
            while number == 100:
                number = 0
                async for message in self.bot.logs_from(channel, limit=100, before=last):
                    number = number + 1
                    if self.bot.user not in message.mentions and message.author.bot != True:
                        if len(message.content.split(" ")) >= 4 and len(message.content) >= 8 and not message.content.startswith("!"):
                            try:
                                ranks[ctx.message.server.id][message.author.id]["posts"] += 1
                            except KeyError:
                                ranks[ctx.message.server.id][message.author.id] = {}
                                ranks[ctx.message.server.id][message.author.id]["posts"] = 1
                                ranks[ctx.message.server.id][message.author.id]["username"] = message.author.name
                    last = message
        dataIO.save_json("data/counter/ranks.json", ranks)
        await self.bot.say("All messages counted")

    @top.command(pass_context=True, no_pm=True, name="display")
    async def top_display(self, ctx):
        "Display top posters"
        ranks = dataIO.load_json("data/counter/ranks.json")
   
        sorted_users = sorted(ranks[ctx.message.server.id], key=lambda x: ranks[ctx.message.server.id][x]["posts"], reverse=True)
        
        top = 10
        if len(sorted_users) < top:
            top = len(sorted_users)
        topfive = sorted_users[:top]
        highscore = "Top Posters:\n"
        place = 1
        for user in topfive:
            highscore += str(place).ljust(len(str(top))+1)
            highscore += (ranks[ctx.message.server.id][user]["username"]+" ").ljust(23-len(str(ranks[ctx.message.server.id][user]["posts"])))
            highscore += str(ranks[ctx.message.server.id][user]["posts"]) + "\n"
            place += 1
            
        if highscore:
            if len(highscore) < 1985:
                await self.bot.say("```py\n"+highscore+"```")
            else:
                await self.bot.say("The leaderboard is too big to be displayed.")
        else:
            await self.bot.say("The server messages have not been counted yet")
    
def check_folders():
    if not os.path.exists("data/economy"):
        print("Creating data/economy folder...")
        os.makedirs("data/economy")

    if not os.path.exists("data/counter"):
        print("Creating data/counter folder...")
        os.makedirs("data/counter")
        
def check_files():

    f = "data/economy/settings.json"
    if not fileIO(f, "check"):
        print("Creating default economy's settings.json...")
        fileIO(f, "save", {})

    f = "data/economy/bank.json"
    if not fileIO(f, "check"):
        print("Creating empty bank.json...")
        fileIO(f, "save", {})
        
    f = "data/counter/ranks.json"
    if not fileIO(f, "check"):
        print("Creating empty ranks.json...")
        fileIO(f, "save", {})
        
def setup(bot):
    global logger
    check_folders()
    check_files()
    bot.add_cog(Counter(bot))
