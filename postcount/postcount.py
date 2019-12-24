import discord

from redbot.core import commands, checks, Config, bot
from redbot.core.utils.chat_formatting import box, humanize_list
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
# https://red-discordbot.readthedocs.io/en/latest/framework_utils.html
# https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/cogs/economy/economy.py

# Message storage information
"""
Settings {
    RequiredWordCount = Number # Like 3 or something
    RequiredLetterCount = Number # Like 8 or something
}
MessageStore = {
    ChannelID = {
        TotalCount = { User: Number } # Total Message count
        FilteredCount = { User: Number } # Total message count that passes requirements
    }
UserArchive = { UserID: DisplayName }
ChannelBlacklist = [ ChannelID ]
"""

# Ideas
# Bot exclusion from leaderboard toggle - Done
# Display leaderboard for a single-range of channel - Done
# Implement channel blacklist - Done - Implemented in the leaderboard
# Implement on message event counter - Done
# Update filtered settings with a command - Done

# commands
class Postcount(commands.Cog):
    """My custom counter cog"""
    def __init__(self):
        self.config = Config.get_conf(self, identifier=108112868100055040, force_registration=True)
        default_guild = {
            "RequiredWordCount": 3,
            "RequiredLetterCount": 8,
            "BlacklistedPrefixes": [],
            "MessageStore": {},
            "UserArchive": {},
            "ChannelBlacklist": []
        }

        self.config.register_guild(**default_guild)

    # Commands

    @checks.admin() # Checks if they have admin role - https://red-discordbot.readthedocs.io/en/latest/framework_checks.html
    @commands.group(invoke_without_command=False)
    async def postset(self, ctx): #Recount group
        """
        Base postset group
        """
        pass

    @checks.admin()
    @postset.group(name="wordcount", invoke_without_command=True)
    async def postset_wordcount(self, ctx, count : int):
        """
        Sets the number of words required to pass the filter
        """
        if count < 0:
            count = 0
        await self.config.guild(ctx.guild).RequiredWordCount.set(int(count))
        await ctx.send("RequiredWordCount set to: {}".format(count))

    @checks.admin()
    @postset.group(name="lettercount", invoke_without_command=True)
    async def postset_lettercount(self, ctx, count : int):
        """
        Sets the number of letters required to pass the filter
        """
        if count < 0:
            count = 0
        await self.config.guild(ctx.guild).RequiredLetterCount.set(int(count))
        await ctx.send("RequiredLetterCount set to: {}".format(count))

    @checks.admin()
    @postset.group(name="blacklistprefix", invoke_without_command=True)
    async def postset_blacklistprefix(self, ctx, prefix : str):
        """
        Adds/Removes a prefix to the blacklist
        """
        async with self.config.guild(ctx.guild).BlacklistedPrefixes() as BlacklistedPrefixes:
            if prefix in BlacklistedPrefixes:
                # list.index(element)
                del BlacklistedPrefixes[BlacklistedPrefixes.index(prefix)]
                await ctx.send("Removed '{}' from BlacklistedPrefixes".format(prefix))
            else:
                BlacklistedPrefixes.append(prefix)
                await ctx.send("Added '{}' to BlacklistedPrefixes".format(prefix))

    @checks.admin()
    @postset.group(name="blacklistchannel", invoke_without_command=True)
    async def postset_blacklistchannel(self, ctx):
        """
        Adds/Removes the mentioned channels to the blacklist.
        """
        channels = ctx.message.channel_mentions
        result = ""
        async with self.config.guild(ctx.guild).ChannelBlacklist() as ChannelBlacklist:
            for channel in channels:
                channel_id = str(channel.id)
                if channel_id in ChannelBlacklist:
                    # list.index(element)
                    del ChannelBlacklist[ChannelBlacklist.index(channel_id)]
                    result += "Removed '{}' from ChannelBlacklist \n".format(channel.name)
                else:
                    ChannelBlacklist.append(channel_id)
                    result += "Added '{}' to ChannelBlacklist \n".format(channel.name)
        if result != "":
            await ctx.send(result)

    @checks.admin()
    @postset.group(name="show", invoke_without_command=True)
    async def postset_show(self, ctx):
        """
        Show currently configured settings
        """
        RequiredWordCount = await self.config.guild(ctx.guild).RequiredWordCount()
        RequiredLetterCount = await self.config.guild(ctx.guild).RequiredLetterCount()
        BlacklistedPrefixes = await self.config.guild(ctx.guild).BlacklistedPrefixes()
        ChannelBlacklist = await self.config.guild(ctx.guild).ChannelBlacklist()
        await ctx.send(box("RequiredWordCount: {}\nRequiredLetterCount: {}\nBlacklistedPrefixes: {}\nChannelBlacklist: {}".format(RequiredWordCount, RequiredLetterCount, BlacklistedPrefixes, ChannelBlacklist)))

    @checks.is_owner()
    @postset.group(name="clear", invoke_without_command=True)
    async def postset_clear(self, ctx):
        """Clears config for the bot. This is global"""
        await self.config.clear_all()
        await ctx.send("Config cleared")
    # Regular count commands

    @checks.admin() # Checks if they have admin role - https://red-discordbot.readthedocs.io/en/latest/framework_checks.html
    @commands.group(name="posts", invoke_without_command=False)
    async def posts(self, ctx): #Recount group
        """
        Base count group
        """
        pass

    @checks.admin() # Checks if they have admin role - https://red-discordbot.readthedocs.io/en/latest/framework_checks.html
    @posts.group(name="count", invoke_without_command=False)
    async def posts_count(self, ctx): #Recount group
        """
        Posts count sub group
        """
        pass

    @checks.admin() # Checks if they have admin role - https://red-discordbot.readthedocs.io/en/latest/framework_checks.html
    @posts_count.group(name="channel", invoke_without_command=True)
    async def posts_count_channel(self, ctx): #Counts the channel the command is mentioned in
        """Counts channel. Can mention multiple servers to specifically recount multiple at once"""
        channelFinished = []
        if ctx.message.channel_mentions != []:
            channelList = ctx.message.channel_mentions # Can allow them to give various channel to scan both - https://discordpy.readthedocs.io/en/latest/api.html#discord.Message.channel_mentions
        else:
            channelList = [ctx.channel]

        async with ctx.channel.typing(): # Will list the bot as typing while it counts - https://discordpy.readthedocs.io/en/latest/api.html#textchannel
            for channel in channelList:
                try:
                    await self.collectChannel(channel)
                    channelFinished.append(channel)
                except discord.errors.Forbidden:
                    pass
                    # await ctx.channel.send('Unable to count {0}. Access Forbidden. Skipping {0}'.format(channel.name))

            await ctx.channel.send('Done counting {0}'.format(humanize_list([c.name for c in channelFinished])))
            #await ctx.channel.send('Done! Count: {}'.format(await self.config.get_raw("MessageStore", ctx.guild.id)))
            #await ctx.channel.send('Done! Count: {}'.format(channelTotal)) # Will send message once above is done

    @checks.admin() # Checks if they have admin role - https://red-discordbot.readthedocs.io/en/latest/framework_checks.html
    @posts_count.group(name="server", invoke_without_command=True)
    async def posts_count_server(self, ctx): #Counts the entire server the command is mentioned in
        """
        Counts the entire server. Goes through all channels the bot can see and view
        """
        channelFinished = []
        channelList = ctx.guild.text_channels

        async with ctx.channel.typing(): # Will list the bot as typing while it counts - https://discordpy.readthedocs.io/en/latest/api.html#textchannel
            for channel in channelList:
                try:
                    await self.collectChannel(channel)
                    channelFinished.append(channel)
                except discord.errors.Forbidden:
                    pass
                    # await ctx.channel.send('Unable to count {0}. Access Forbidden. Skipping {0}'.format(channel.name))
            await ctx.channel.send('Done counting {}'.format(humanize_list([c.name for c in channelFinished])))

    @posts.group(name="leaderboard", invoke_without_command=True)
    async def posts_leaderboard(self, ctx):
        """
        Gets the leaderboard excluding filtered messages
        """
        guild = ctx.guild
        author = ctx.author

        channel_list = ctx.message.channel_mentions # Can allow them to give various channel to scan both - https://discordpy.readthedocs.io/en/latest/api.html#discord.Message.channel_mentions

        sorted_list = await self.get_leaderboard(guild, channel_list)
        highscores = [] # testing menu

        try:
            post_len = len(str(sorted_list[0][1])) # Get the first result which will have the max character length
            pound_len = len(str(len(sorted_list[0]))) # To get the highest number/position (Most characters) in the list of users.
        except IndexError:
            post_len = 3
            pound_len = 2

        # Creates the header of the message
        header = "{pound:{pound_len}}{score:{post_len}}{name:2}\n".format(
            pound="#",
            name="Name",
            score="Posts",
            post_len=post_len + 6, #bal_len + 6
            pound_len=pound_len + 3 #pound_len + 3,
        )
        pos = 1 # Starting position 1
        temp_msg = header # Setting temp_msg to the header since we append everything after

        for user_data in sorted_list:
            member = guild.get_member(int(user_data[0]))
            posts = user_data[1]
            if member == None: #If user isn't in the server we will encounter an error
                UserArchive = await self.config.guild(guild).UserArchive()
                user_id = int(user_data[0])
                user_display_name = UserArchive[user_data[0]]
            else:
                user_id = member.id
                user_display_name = member.display_name

            if user_id != ctx.bot.user.id: # To skip bot user
                if user_id != author.id: # Gives normal score to everyone else
                    temp_msg += (
                        f"{f'{pos}.': <{pound_len+2}} "
                        f"{posts: <{post_len + 5}} {user_display_name}\n"
                    )
                else: # Gives your score a highlighted ID
                    temp_msg += (
                        f"{f'{pos}.': <{pound_len+2}} "
                        f"{posts: <{post_len + 5}} "
                        f"<<{user_display_name}>>\n"
                    )
            if pos % 10 == 0:
                highscores.append(box(temp_msg, lang="md"))
                temp_msg = header
            pos += 1

        if temp_msg != header:
            highscores.append(box(temp_msg, lang="md"))

        if highscores:
            await menu(ctx, highscores, DEFAULT_CONTROLS)
        #Test to see if bot user and excluding it from the leaderboard. Could also update the list I'm iterating over to include 1 extra user
        #await ctx.channel.send(box(temp_msg))

    @posts_leaderboard.group(name="total", invoke_without_command=True)
    async def posts_leaderboard_total(self, ctx):
        """
        Gets the full leaderboard including filtered messages
        """
        guild = ctx.guild
        author = ctx.author

        channel_list = ctx.message.channel_mentions # Can allow them to give various channel to scan both - https://discordpy.readthedocs.io/en/latest/api.html#discord.Message.channel_mentions

        sorted_list = await self.get_leaderboard(guild, channel_list, filtered=False)
        highscores = [] # testing menu

        try:
            post_len = len(str(sorted_list[0][1])) # Get the first result which will have the max character length
            pound_len = len(str(len(sorted_list[0]))) # To get the highest number/position (Most characters) in the list of users.
        except IndexError:
            post_len = 3
            pound_len = 2

        # Creates the header of the message
        header = "{pound:{pound_len}}{score:{post_len}}{name:2}\n".format(
            pound="#",
            name="Name",
            score="Posts",
            post_len=post_len + 6, #bal_len + 6
            pound_len=pound_len + 3 #pound_len + 3,
        )
        pos = 1 # Starting position 1
        temp_msg = header # Setting temp_msg to the header since we append everything after

        for user_data in sorted_list:
            member = guild.get_member(int(user_data[0]))
            posts = user_data[1]
            if member == None: #If user isn't in the server we will encounter an error
                UserArchive = await self.config.guild(guild).UserArchive()
                user_id = int(user_data[0])
                user_display_name = UserArchive[user_data[0]]
            else:
                user_id = member.id
                user_display_name = member.display_name

            if user_id != ctx.bot.user.id: # To skip bot user
                if user_id != author.id: # Gives normal score to everyone else
                    temp_msg += (
                        f"{f'{pos}.': <{pound_len+2}} "
                        f"{posts: <{post_len + 5}} {user_display_name}\n"
                    )
                else: # Gives your score a highlighted ID
                    temp_msg += (
                        f"{f'{pos}.': <{pound_len+2}} "
                        f"{posts: <{post_len + 5}} "
                        f"<<{user_display_name}>>\n"
                    )
            if pos % 10 == 0:
                highscores.append(box(temp_msg, lang="md"))
                temp_msg = header
            pos += 1

        if temp_msg != header:
            highscores.append(box(temp_msg, lang="md"))

        if highscores:
            await menu(ctx, highscores, DEFAULT_CONTROLS)
        #Test to see if bot user and excluding it from the leaderboard. Could also update the list I'm iterating over to include 1 extra user
        #await ctx.channel.send(box(temp_msg))

    # Events
    @commands.Cog.listener('on_message') # Executes the below command when message recieved
    async def on_message(self, message):
        #RequiredWordCount = await self.config.guild(message.guild).RequiredWordCount()
        #RequiredLetterCount = await self.config.guild(message.guild).RequiredLetterCount()

        # Need to do this due to quick of the Data store. All int keys are converted to strings when saved. So it allows you to use int the first time, then you have to use STR every other time
        channel_id = str(message.channel.id)
        author_id = str(message.author.id)

        async with self.config.guild(message.channel.guild).MessageStore() as MessageStore:
            # MessageStore[channel.id] = channel_total
            #if (len(message.content.split()) >= RequiredWordCount) and (len(message.content) >= RequiredLetterCount):
            if await self.filter_check(message):
                try:
                    MessageStore[channel_id]["TotalCount"][author_id] += 1
                except KeyError: # If the author ID isn't already in the dict
                    if channel_id not in MessageStore:
                        MessageStore[channel_id] = {"TotalCount" : {}, "FilteredCount" : {} }
                    MessageStore[channel_id]["TotalCount"][author_id] = 1
            else:
                try:
                    MessageStore[channel_id]["FilteredCount"][author_id] += 1
                except KeyError: # If the author ID isn't already in the dict
                    if channel_id not in MessageStore:
                        MessageStore[channel_id] = {"TotalCount" : {}, "FilteredCount" : {} }
                    MessageStore[channel_id]["FilteredCount"][author_id] = 1
        # Archive users display names for future use
        async with self.config.guild(message.channel.guild).UserArchive() as UserArchive:
            UserArchive[message.author.id] = message.author.display_name


    # General Functions
    async def collectChannel(self, channel):
        """
        Will return data in the below format. Whatever calls this is in charge of attaching it to the server and channel
            {
            TotalCount { UserID: Number }
            FilteredCount { UserID: Number }
            }
        """
        channel_total = {"TotalCount" : {}, "FilteredCount" : {} }

        # Need to do this due to quick of the Data store. All int keys are converted to strings when saved. So it allows you to use int the first time, then you have to use STR every other time
        channel_id = str(channel.id)

        #RequiredWordCount = await self.config.guild(channel.guild).RequiredWordCount()
        #RequiredLetterCount = await self.config.guild(channel.guild).RequiredLetterCount()

        async for message in channel.history(oldest_first=True, limit=None):
            author_id = str(message.author.id)
            # Checks if message passes filter check
            #if (len(message.content.split()) >= RequiredWordCount) and (len(message.content) >= RequiredLetterCount):
            if await self.filter_check(message):
                try:
                    channel_total["TotalCount"][author_id] += 1
                except KeyError: # If the author ID isn't already in the dict
                    channel_total["TotalCount"][author_id] = 1
            else:
                try:
                    channel_total["FilteredCount"][author_id] += 1
                except KeyError: # If the author ID isn't already in the dict
                    channel_total["FilteredCount"][author_id] = 1
            # Archive users display names for future use
            async with self.config.guild(channel.guild).UserArchive() as UserArchive:
                UserArchive[author_id] = message.author.display_name

        # I did it this way so it doesn't hold the MessageStore data open for long.
        async with self.config.guild(channel.guild).MessageStore() as MessageStore:
            MessageStore[channel_id] = channel_total
        # return channel_total


    async def get_leaderboard(self, guild:discord.Guild = None, channel_list=[], filtered=True):
        """
        Gets the top posting get_leaderboard
        """
        # Creates a list of provided channels so it can compare the ID with the database
        ChannelBlacklist = await self.config.guild(guild).ChannelBlacklist()
        channel_id_list = [str(c.id) for c in channel_list]

        #for provided_channel in channel_list:
            #channel_id_list.append(provided_channel.id)

        if guild is None:
            raise TypeError("Expected a guild, got NoneType object instead!")

        total_user_posts = {}
        # Need to update raw_channel to MessageStore
        MessageStore = await self.config.guild(guild).MessageStore()
        for channel in MessageStore:
            if (channel_list == []) or (channel in channel_id_list): # To allow specific channels to only be included
                if channel not in ChannelBlacklist:
                    for user in MessageStore[channel]["TotalCount"]:
                        try:
                            total_user_posts[user] += MessageStore[channel]["TotalCount"][user]
                        except KeyError:
                            total_user_posts[user] = MessageStore[channel]["TotalCount"][user]
                    if filtered == False:
                        for user in MessageStore[channel]["FilteredCount"]:
                            try:
                                total_user_posts[user] += MessageStore[channel]["FilteredCount"][user]
                            except KeyError:
                                total_user_posts[user] = MessageStore[channel]["FilteredCount"][user]

        #Sorts based on the post count of each user
        sorted_list = sorted(total_user_posts.items(), key=lambda x: x[1], reverse=True)
        return sorted_list

    async def filter_check(self, message): # To unify the filter rules across the board and have then managed from a central function
        Result = False
        RequiredWordCount = await self.config.guild(message.guild).RequiredWordCount()
        RequiredLetterCount = await self.config.guild(message.guild).RequiredLetterCount()
        BlacklistedPrefixes = tuple(await self.config.guild(message.guild).BlacklistedPrefixes())

        if not message.author.bot:
            if (len(message.content.split()) >= RequiredWordCount):
                if (len(message.content) >= RequiredLetterCount):
                    if not message.content.startswith(BlacklistedPrefixes):
                        Result = True

        return Result
# https://discordpy.readthedocs.io/en/latest/api.html#event-reference
