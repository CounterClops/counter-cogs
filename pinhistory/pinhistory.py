import discord

from redbot.core import commands, checks, Config, bot
from redbot.core.utils.chat_formatting import box, humanize_list
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
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
            "archive_channel": [], # Channels to archive the pinned messages to
        }

        self.config.register_guild(**default_guild)

    # Commands
    @checks.admin() # Checks if they have admin role - https://red-discordbot.readthedocs.io/en/latest/framework_checks.html
    @commands.group(invoke_without_command=False)
    async def pinhistoy(self, ctx): #Recount group
        """
        Base postset group
        """
        # Should display current settings
        await ctx.send("```{}```".format(self.config.guild(channel.guild)))

    @checks.admin()
    @pinhistoy.group(name="pinlimit")
    async def pinhistoy_pinlimit(self, ctx, pin_limit : int):
        """
        Set the number of pins allowed in a monitored channel
        """
        self.config.guild(channel.guild).pin_limit = pin_limit
        await ctx.send("Set pin limit to {}".format(pin_limit))

    @checks.admin()
    @pinhistoy.group(name="managepins")
    async def pinhistoy_managepins(self, ctx):
        """
        Toggle if pinned messages should be managed. EG, deleted once they go over pin limit
        """
        self.config.guild(channel.guild).manage_pins = not self.config.guild(channel.guild).manage_pins
        await ctx.send("Set pin management to {}".format(self.config.guild(channel.guild).manage_pins))


    @checks.admin()
    @pinhistoy.group(name="enable")
    async def pinhistoy_monitor(self, ctx, channel=None):
        """
        Monitors channel, if none is given it'll use the one in context. If one is mentioned, it'll use that one
        """
        if channel == None:
            if ctx.channel.id not in channel.id in self.config.guild(channel.guild).monitored_channels:
                self.config.guild(channel.guild).monitored_channels.append(ctx.channel.id)
                await ctx.send("Enabled monitoring for {}".format(channel.name))
            else:
                self.config.guild(channel.guild).monitored_channels.remove(ctx.channel.id)
                await ctx.send("Disabled monitoring for {}".format(channel.name))

    # https://leovoel.github.io/embed-visualizer/
    # https://cog-creators.github.io/discord-embed-sandbox/

    def create_embed(message):
        "Create the correctly formatted embed for pinned messages"
        # Create embed using information from message
        embed_message = discord.Embed(description=message.content)
        embed_message.set_author(name=message.author.display_name, url="https://discord.com/users/{}".format(message.author.id), icon_url=message.author.avatar_url)
        embed_message.set_footer(text=message.created_at)
        return embed_message

    # https://discordpy.readthedocs.io/en/latest/api.html#discord.on_guild_channel_pins_update
    # Monitored Events
    @commands.Cog.listener('on_guild_channel_pins_update') # Executes the below command when a channels pinned messages changes
    async def on_pin_update(self, channel, last_pin):
        if (channel.id in self.config.guild(channel.guild).monitored_channels) and (last_pin != None):
            # Check if this pin hasn't already been archived
            if last_pin.id not in self.config.guild(channel.guild).pin_history:
                # Get list of attachments from message
                # Save list of attachment objects to a list of file like objects
                # Send embed with provided attachments
                embed_message = create_embed(last_pin)
                for channel_id in await fetch_channel(self.config.guild(channel.guild).archive_channel)
                    channel = await fetch_channel(channel_id)
                    await channel.send(embed=embed_message)
                self.config.guild(channel.guild).pin_history.append(last_pin.id)
                pass
