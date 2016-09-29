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

class BankError(Exception):
    pass

class AccountAlreadyExists(BankError):
    pass

class NoAccount(BankError):
    pass

class InsufficientBalance(BankError):
    pass

class NegativeValue(BankError):
    pass

class SameSenderAndReceiver(BankError):
    pass

class Bank:
    def __init__(self, bot, file_path):
        self.accounts = dataIO.load_json(file_path)
        self.bot = bot

    def create_account(self, user, *, initial_balance=0):
        server = user.server
        if not self.account_exists(user):
            if server.id not in self.accounts:
                self.accounts[server.id] = {}
            if user.id in self.accounts: # Legacy account
                balance = self.accounts[user.id]["balance"]
            else:
                balance = initial_balance
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            account = {"name" : user.name,
                       "balance" : balance,
                       "created_at" : timestamp
                      }
            self.accounts[server.id][user.id] = account
            self._save_bank()
            return self.get_account(user)
        else:
            raise AccountAlreadyExists()

    def account_exists(self, user):
        try:
            self._get_account(user)
        except NoAccount:
            return False
        return True

    def get_server_accounts(self, server):
        if server.id in self.accounts:
            raw_server_accounts = deepcopy(self.accounts[server.id])
            accounts = []
            for k, v in raw_server_accounts.items():
                v["id"] = k
                v["server"] = server
                acc = self._create_account_obj(v)
                accounts.append(acc)
            return accounts
        else:
            return []

    def get_all_accounts(self):
        accounts = []
        for server_id, v in self.accounts.items():
            server = self.bot.get_server(server_id)
            if server is None:# Servers that have since been left will be ignored
                continue      # Same for users_id from the old bank format
            raw_server_accounts = deepcopy(self.accounts[server.id])
            for k, v in raw_server_accounts.items():
                v["id"] = k
                v["server"] = server
                acc = self._create_account_obj(v)
                accounts.append(acc)
        return accounts

    def get_balance(self, user):
        account = self._get_account(user)
        return account["balance"]

    def get_account(self, user):
        acc = self._get_account(user)
        acc["id"] = user.id
        acc["server"] = user.server
        return self._create_account_obj(acc)

    def _create_account_obj(self, account):
        account["member"] = account["server"].get_member(account["id"])
        account["created_at"] = datetime.strptime(account["created_at"],
                                                  "%Y-%m-%d %H:%M:%S")
        Account = namedtuple("Account", "id name balance "
                             "created_at server member")
        return Account(**account)

    def _save_bank(self):
        dataIO.save_json("data/economy/bank.json", self.accounts)

    def _get_account(self, user):
        server = user.server
        try:
            return deepcopy(self.accounts[server.id][user.id])
        except KeyError:
            raise NoAccount()
        
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
    
def check_folders():
    if not os.path.exists("data/economy"):
        print("Creating data/economy folder...")
        os.makedirs("data/economy")

def check_files():

    f = "data/economy/settings.json"
    if not fileIO(f, "check"):
        print("Creating default economy's settings.json...")
        fileIO(f, "save", {})

    f = "data/economy/bank.json"
    if not fileIO(f, "check"):
        print("Creating empty bank.json...")
        fileIO(f, "save", {})
        
def setup(bot):
    global logger
    check_folders()
    check_files()
    bot.add_cog(CounterCommands(bot))
