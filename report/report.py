import discord
from discord.ext import commands
from .utils.dataIO import fileIO, dataIO
from .utils import checks
from datetime import datetime
from __main__ import send_cmd_help, settings
import logging
import os

class Report:
    """Adds in a report system"""
    def __init__(self, bot):
        self.bot = bot
        self.reports = dataIO.load_json("data/counter/reports.json")

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def report(self, ctx, user : discord.Member, points : int, *reason : str):
        """Lodge a user report"""
        if points <= 50:
            try:
                self.reports[ctx.message.server.id][user.id]
            except KeyError:
                if ctx.message.server.id not in self.reports:
                    self.reports[ctx.message.server.id] = {}
                self.reports[ctx.message.server.id][user.id]= {}
            reason = " ".join(reason)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report = {"name" : user.name,
                       "reason" : reason,
                       "points" : points,
                       "active" : True,
                       "created_by" : ctx.message.author.name,
                       "created_at" : timestamp
                      }

            if self.reports[ctx.message.server.id][user.id]:
                reportid = len(self.reports[ctx.message.server.id][user.id])
            else:
                reportid = 0
                
            self.reports[ctx.message.server.id][user.id][reportid] = report
            dataIO.save_json("data/counter/reports.json", self.reports)
            await self.bot.say("Report lodged")

            total = 0
            for v in self.reports[ctx.message.server.id][user.id]:
                if self.reports[ctx.message.server.id][user.id][v]["active"]:
                    total += self.reports[ctx.message.server.id][user.id][v]["points"]
            await self.bot.say("{0} has {1}/100".format(user.name, str(total)))
        else:
            await self.bot.say("You cannot give more than 50 points for a single offence\nReport has been stopped")

    @commands.command(pass_context=True) #!showreports @Aethex#0394 
    @checks.admin_or_permissions(administrator=True)
    async def showreports(self, ctx, user : discord.Member):
        all_reports = "{0} has been reported for\n".format(user.name)
        total = 0
        
        try:
            self.reports[ctx.message.server.id][user.id]
        except KeyError:
            if ctx.message.server.id not in self.reports:
                self.reports[ctx.message.server.id] = {}
                
        if self.reports[ctx.message.server.id][user.id]:
            for v in self.reports[ctx.message.server.id][user.id]:
                all_reports += """{0} (Username at time) : reported for "{1}" worth {2} on {3} by {4}\n""".format(self.reports[ctx.message.server.id][user.id][v]["name"], self.reports[ctx.message.server.id][user.id][v]["reason"], self.reports[ctx.message.server.id][user.id][v]["points"], self.reports[ctx.message.server.id][user.id][v]["created_at"], self.reports[ctx.message.server.id][user.id][v]["created_by"])
                if self.reports[ctx.message.server.id][user.id][v]["active"]:
                    total += self.reports[ctx.message.server.id][user.id][v]["points"]
                if (len(all_reports) - all_reports.count(' ')) > 1500:
                    await self.bot.say("```"+all_reports+"```")
                    all_reports = ""
                
            await self.bot.say("```"+all_reports+"\nTotal user score: "+str(total)+"/100"+"```")
        else:
            await self.bot.say("This user has no reports against them")
            
    
def check_folders():
    if not os.path.exists("data/counter"):
        print("Creating data/counter folder...")
        os.makedirs("data/counter")

def check_files():

    f = "data/counter/reports.json"
    if not fileIO(f, "check"):
        print("Creating default reports.json...")
        fileIO(f, "save", {})
        
def setup(bot):
    global logger
    check_folders()
    check_files()
    bot.add_cog(Report(bot))
    
