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

    @commands.group(pass_context=True)
    async def report(self, ctx):
        """Lodge moderator reports on users"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

    @report.command(pass_context=True, no_pm=True, name="add")
    @checks.admin_or_permissions(administrator=True)
    async def report_add(self, ctx, user : discord.Member, points : int, *reason : str):
        """Lodge a user report"""
        if points <= 100:
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

            if user.id in self.reports[ctx.message.server.id]:
                reportid = len(self.reports[ctx.message.server.id][user.id])
            else:
                reportid = 0
                
            self.reports[ctx.message.server.id][user.id][str(reportid)] = report
            dataIO.save_json("data/counter/reports.json", self.reports)
            self.reports = dataIO.load_json("data/counter/reports.json")
            await self.bot.say("Report lodged")

            total = 0
            for v in self.reports[ctx.message.server.id][user.id]:
                if self.reports[ctx.message.server.id][user.id][v]["active"]:
                    total += self.reports[ctx.message.server.id][user.id][v]["points"]
            await self.bot.say("{0} has {1}/100".format(user.name, str(total)))
        else:
            await self.bot.say("You can only give a max of 100.")

    @report.command(pass_context=True, no_pm=True, name="deactivate")
    @checks.admin_or_permissions(administrator=True)
    async def report_deactivate(self, ctx, user : discord.Member, reportid : int):
        "Deactivate a report"
        try:
            self.reports[ctx.message.server.id][user.id]
        except KeyError:
            if ctx.message.server.id not in self.reports:
                self.reports[ctx.message.server.id] = {}
                await self.bot.say("No reports on this user")

        if user.id in self.reports[ctx.message.server.id]:
            reports = len(self.reports[ctx.message.server.id][user.id])
            if reportid < reports:
                if self.reports[ctx.message.server.id][user.id][str(reportid)]["active"] == True:
                    self.reports[ctx.message.server.id][user.id][str(reportid)]["active"] = False
                    dataIO.save_json("data/counter/reports.json", self.reports)
                    await self.bot.say("Report deactivated")
                else:
                    await self.bot.say("That report is already disactivated")
            else:
                await self.bot.say("There are no reports that match that id")

    @report.command(pass_context=True, no_pm=True, name="activate")
    @checks.admin_or_permissions(administrator=True)
    async def report_activate(self, ctx, user : discord.Member, reportid : int):
        "Reactivate a deactivated report"
        try:
            self.reports[ctx.message.server.id][user.id]
        except KeyError:
            if ctx.message.server.id not in self.reports:
                self.reports[ctx.message.server.id] = {}
                await self.bot.say("No reports on this user")

        if user.id in self.reports[ctx.message.server.id]:
            reports = len(self.reports[ctx.message.server.id][user.id])
            if reportid < reports:
                if self.reports[ctx.message.server.id][user.id][str(reportid)]["active"] == False:
                    self.reports[ctx.message.server.id][user.id][str(reportid)]["active"] = True
                    dataIO.save_json("data/counter/reports.json", self.reports)
                    await self.bot.say("Report activated")
                else:
                    await self.bot.say("That report is already active")
            else:
                await self.bot.say("There are no reports that match that id")

    @report.command(pass_context=True, no_pm=True, name="all")
    @checks.admin_or_permissions(administrator=True)
    async def reports_all(self, ctx, user : discord.Member=None):
        "Show all the reports that have been lodged against a user or in the server"
        if user == None:
            try:
                self.reports[ctx.message.server.id]
            except KeyError:
                if ctx.message.server.id not in self.reports:
                    self.reports[ctx.message.server.id] = {}
                    await self.bot.say("No reports")
                    return
            all_reports = ""
            total = 0
                    
            for user in self.reports[ctx.message.server.id]:
                report_num = len(self.reports[ctx.message.server.id][user])
                for id in range(report_num):
                    v = str(id)
                    all_reports += """{0}-{1} (Active={6}): reported for "{2}" worth {3} on {4} by {5}\n""".format(v, self.reports[ctx.message.server.id][user][v]["name"], self.reports[ctx.message.server.id][user][v]["reason"], self.reports[ctx.message.server.id][user][v]["points"], self.reports[ctx.message.server.id][user][v]["created_at"], self.reports[ctx.message.server.id][user][v]["created_by"],self.reports[ctx.message.server.id][user][v]["active"])
                    if self.reports[ctx.message.server.id][user][v]["active"]:
                        total += self.reports[ctx.message.server.id][user][v]["points"]
                    if int(len(all_reports) - all_reports.count(' ')) > 1500:
                        await self.bot.say("```"+all_reports+"```")
                        all_reports = ""
                        
            if all_reports != "":
                await self.bot.say("```All reports\n"+all_reports+"```")
            else:
                await self.bot.say("This user has no reports against them")  
        else:
            try:
                self.reports[ctx.message.server.id][user.id]
            except KeyError:
                if ctx.message.server.id not in self.reports:
                    self.reports[ctx.message.server.id] = {}
                    await self.bot.say("No reports")
                    return
                
            all_reports = "{0} has been reported for\n".format(user.name)
            total = 0
                    
            if user.id in self.reports[ctx.message.server.id]:
                report_num = len(self.reports[ctx.message.server.id][user.id])
                for id in range(report_num):
                    v = str(id)
                    all_reports += """{0}-{1} (Active={6}): reported for "{2}" worth {3} on {4} by {5}\n""".format(v, self.reports[ctx.message.server.id][user.id][v]["name"], self.reports[ctx.message.server.id][user.id][v]["reason"], self.reports[ctx.message.server.id][user.id][v]["points"], self.reports[ctx.message.server.id][user.id][v]["created_at"], self.reports[ctx.message.server.id][user.id][v]["created_by"],self.reports[ctx.message.server.id][user.id][v]["active"])
                    if self.reports[ctx.message.server.id][user.id][v]["active"]:
                        total += self.reports[ctx.message.server.id][user.id][v]["points"]
                    if int(len(all_reports) - all_reports.count(' ')) > 1500:
                        await self.bot.say("```"+all_reports+"```")
                        all_reports = ""
                await self.bot.say("```"+all_reports+"\nTotal user score: "+str(total)+"/100"+"```")
            else:
                await self.bot.say("This user has no reports against them")                

    @report.command(pass_context=True, no_pm=True, name="list")
    @checks.admin_or_permissions(administrator=True)
    async def report_list(self, ctx):
        "Lists all users in negative standing"
        message = ""
        try:
            self.reports[ctx.message.server.id]
        except KeyError:
            if ctx.message.server.id not in self.reports:
                self.reports[ctx.message.server.id] = {}
                await self.bot.say("No user's have been reported")
                return

        for user in self.reports[ctx.message.server.id]:
            user_total = 0
            for report in self.reports[ctx.message.server.id][user]:
                if self.reports[ctx.message.server.id][user][report]["active"] == True:
                    user_total += self.reports[ctx.message.server.id][user][report]["points"]
            if user_total > 0:
                try:
                    user_name = discord.utils.get(ctx.message.server.members, id=user).name
                except AttributeError:
                    user_name = self.reports[ctx.message.server.id][user][str(len(self.reports[ctx.message.server.id][user])-1)]["name"]
                message += "{0} has {1}/100\n".format(user_name, user_total)

        if message != "":
            message = "```These users have active logs against them\n" + message + "```"
        else:
            message = "No users have active reports on this server"
        await self.bot.say(message)
            
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
