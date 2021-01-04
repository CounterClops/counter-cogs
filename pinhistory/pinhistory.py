import discord

from redbot.core import commands, checks, Config, bot
from redbot.core.utils.chat_formatting import box, humanize_list
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

#timezone
#from pytz import timezone
from datetime import datetime, timezone

# https://red-discordbot.readthedocs.io/en/latest/framework_utils.html
# https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/cogs/economy/economy.py

# https://discordpy.readthedocs.io/en/latest/api.html#discord.TextChannel.send
# https://discordpy.readthedocs.io/en/latest/api.html#discord.Message.attachments
# https://discordpy.readthedocs.io/en/latest/api.html#discord.Attachment

# commands
class PinHistory(commands.Cog):
    """My custom counter cog"""
    def __init__(self):
        self.config = Config.get_conf(self, identifier=108586980896678, force_registration=True)
        default_guild = {
            "pin_limit": 50, # Maximum number of pinned messages
            "manage_pins": True, # Whether the bot should manage pinned messages in the monitored channels (Remove old pins etc)
            "pin_history": [], # List of ID's for all pinned messages that have been archived
            "monitored_channels": [],  # Channels to monitor for changes in pins
            "archive_channels": [], # Channels to archive the pinned messages to
        }

        self.config.register_guild(**default_guild)

    # Commands
    @checks.admin() # Checks if they have admin role - https://red-discordbot.readthedocs.io/en/latest/framework_checks.html
    @commands.group(invoke_without_command=False)
    async def pinhistory(self, ctx): #Recount group
        """
        Base postset group
        """
        pass


    @checks.admin()
    @pinhistory.group(name="settings", invoke_without_command=True)
    async def pinhistory_settings(self, ctx):
        """
        Display current settings
        """
        # Should display current settings
        settings = await self.config.guild(ctx.channel.guild).get_raw()
        await ctx.send("```{}```".format(str(settings)))

    @checks.admin()
    @pinhistory.group(name="pinlimit", invoke_without_command=True)
    async def pinhistory_pinlimit(self, ctx, new_pin_limit : int):
        """
        Set the number of pins allowed in a monitored channel
        """
        async with self.config.guild(ctx.channel.guild).pin_limit() as pin_limit:
            pin_limit = new_pin_limit
            await ctx.send("Set pin limit to {}".format(pin_limit))

    @checks.admin()
    @pinhistory.group(name="managepins", invoke_without_command=True)
    async def pinhistory_managepins(self, ctx):
        """
        Toggle if pinned messages should be managed. EG, deleted once they go over pin limit
        """
        async with self.config.guild(ctx.channel.guild).manage_pins() as manage_pins:
            manage_pins = not manage_pins
            await ctx.send("Set pin management to {}".format(new_value))

    @checks.admin()
    @pinhistory.group(name="toggle", invoke_without_command=False)
    async def pinhistory_toggle(self, ctx):
        pass

    @checks.admin()
    @pinhistory_toggle.group(name="monitor", invoke_without_command=True)
    async def pinhistory_toggle_monitor(self, ctx, channel=None):
        """
        Monitors channel, if none is given it'll use the one in context. If one is mentioned, it'll use that one
        """
        if channel == None:
            channel = ctx.channel
        async with self.config.guild(channel.guild).monitored_channels() as monitored_channels:
            if channel.id not in monitored_channels:
                monitored_channels.append(channel.id)
                await ctx.send("Enabled monitoring for {}".format(channel.name))
            else:
                monitored_channels.remove(channel.id)
                await ctx.send("Disabled monitoring for {}".format(channel.name))

    @checks.admin()
    @pinhistory_toggle.group(name="archive", invoke_without_command=True)
    async def pinhistory_toggle_archive(self, ctx, channel=None):
        """
        Monitors channel, if none is given it'll use the one in context. If one is mentioned, it'll use that one
        """
        if channel == None:
            channel = ctx.channel
        async with self.config.guild(channel.guild).archive_channels() as archive_channels:
            if channel.id not in archive_channels:
                archive_channels.append(channel.id)
                await ctx.send("Enabled archiving to {}".format(channel.name))
            else:
                archive_channels.remove(channel.id)
                await ctx.send("Disabled archiving for {}".format(channel.name))

    # https://leovoel.github.io/embed-visualizer/
    # https://cog-creators.github.io/discord-embed-sandbox/

    def create_embed(self, message):
        "Create the correctly formatted embed for pinned messages"
        # Create embed using information from message
        embed_message = discord.Embed(description=message.content, timestamp=datetime.replace(message.created_at, tzinfo=timezone.utc))
        embed_message.set_author(name=message.author.display_name, url="https://discord.com/users/{}".format(message.author.id), icon_url=message.author.avatar_url)
        embed_message.set_thumbnail(message.author.avatar_url)
        # message_date = timezone("UTC").localize(message.created_at).astimezone("Australia/Perth").strftime(r"%A, %X, %-d/%m/%Y %Z")
        # message_date = datetime.replace(message.created_at, tzinfo=timezone.utc)
        # Australia/Perth
        embed_message.set_footer(text="Posted")
        return embed_message

    # https://discordpy.readthedocs.io/en/latest/api.html#discord.on_guild_channel_pins_update
    # Monitored Events
    @commands.Cog.listener('on_guild_channel_pins_update') # Executes the below command when a channels pinned messages changes
    async def on_pin_update(self, channel, last_pin):
        monitored_channels = await self.config.guild(channel.guild).monitored_channels()
        archive_channels = await self.config.guild(channel.guild).archive_channels()
        if (channel.id in monitored_channels) and (last_pin != None):
            # Check if this pin hasn't already been archived
            last_pinned_message = (await channel.pins())[0]
            async with self.config.guild(channel.guild).pin_history() as pin_history:
                if last_pinned_message.id not in pin_history:
                    # Get list of attachments from message
                    # Save list of attachment objects to a list of file like objects
                    # Send embed with provided attachments
                    embed_message = self.create_embed(last_pinned_message)
                    for channel_id in archive_channels:
                        channel = channel.guild.get_channel(channel_id)
                        await channel.send(embed=embed_message)
                    pin_history.append(last_pinned_message.id)
