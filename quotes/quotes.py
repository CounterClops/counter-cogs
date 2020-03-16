import discord
from random import choice as randchoice

from redbot.core import commands, checks, Config, bot
from redbot.core.utils.chat_formatting import box, humanize_list
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
# https://red-discordbot.readthedocs.io/en/latest/framework_utils.html
# https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/cogs/economy/economy.py

# Message storage information
"""
quote_list = []
"""

# commands
class Quotes(commands.Cog):
    """My custom counter cog"""
    def __init__(self):
        self.config = Config.get_conf(self, identifier=108112868100055040420, force_registration=True)
        default_guild = {
            "quote_list": []
        }
        self.config.register_guild(**default_guild)

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx): #Recount group
        """
        Prints a random quote
        """
        quote_list = await self.config.guild(ctx.guild).quote_list()
        if quote_list != []:
            quote = randchoice(quote_list)
            await ctx.send(box(f"{quote}"))

    @checks.admin()
    @quote.group(name="add", invoke_without_command=True)
    async def quote_add(self, ctx, *, quote : str):
        """
        Adds a quote to the quote list
        """
        async with self.config.guild(ctx.guild).quote_list() as quote_list:
            quote_list.append(quote)
        await ctx.send(f'Added "{quote}"')

    @checks.admin()
    @quote.group(name="del", invoke_without_command=True)
    async def quote_del(self, ctx, quote_pos : int):
        """
        Deletes a quote from the quote list
        """
        # make sure pos starts at 1
        if quote_pos > 0:
            actual_quote_pos = quote_pos - 1
            async with self.config.guild(ctx.guild).quote_list() as quote_list:
                if actual_quote_pos < len(quote_list):
                    removed_quote = quote_list.pop(actual_quote_pos)
            await ctx.send(f'Removed "{removed_quote}"')

    @quote.group(name="all", invoke_without_command=True)
    async def quote_all(self, ctx):
        """
        Prints all a list of all quotes
        """
        quote_list = await self.config.guild(ctx.guild).quote_list()
        pos = 1
        quote_groups = []
        quote_pos_len = len(str(len(quote_list))) # Gets the length of the largest quote number
        temp_msg = ""

        for quote in quote_list:
            temp_msg += (
                    f"{f'{pos}': <{quote_pos_len+2}}{quote}\n\n"
                    )
            if pos % 5 == 0:
                quote_groups.append(box(temp_msg, lang="md"))
                temp_msg = ""
            pos += 1

        if temp_msg != "":
            quote_groups.append(box(temp_msg, lang="md"))

        await menu(ctx, quote_groups, DEFAULT_CONTROLS)
