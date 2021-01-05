import discord

from redbot.core import commands, checks, Config, bot
from redbot.core.utils.chat_formatting import box, humanize_list
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from io import BytesIO
import os
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
            "pin_limit": 48, # Maximum number of pinned messages
            "manage_pins": True, # Whether the bot should manage pinned messages in the monitored channels (Remove old pins etc)
            "reupload_images": False,
            "pin_history": [], # List of ID's for all pinned messages that have been archived
            "monitored_channels": [],  # Channels to monitor for changes in pins
            "archive_channels": [] # Channels to archive the pinned messages to
        }

        self.config.register_guild(**default_guild)

    # Commands
    @checks.admin() # Checks if they have admin role - https://red-discordbot.readthedocs.io/en/latest/framework_checks.html
    @commands.group(invoke_without_command=False)
    async def pinhistory(self, ctx): #Recount group
        """
        Commands related to controlling the automatic pin management / archiving
        """
        pass

    @checks.admin()
    @pinhistory.group(name="clear", invoke_without_command=False)
    async def pinhistory_clear(self, ctx):
        """
        Sub commands allow different options / history to be cleared
        """
        pass

    @checks.admin()
    @pinhistory_clear.group(name="history", invoke_without_command=True)
    async def pinhistory_clear_history(self, ctx):
        """
        Clears all recorded pin history
        """
        async with self.config.guild(ctx.guild).pin_history() as pin_history:
            pin_history.clear()
        await ctx.send("Cleared pin history")

    @checks.admin()
    @pinhistory_clear.group(name="all", invoke_without_command=True)
    async def pinhistory_clear_all(self, ctx):
        """
        Clears pin history along with configured monitor/archive channels
        """
        async with self.config.guild(ctx.guild).pin_history() as pin_history:
            pin_history.clear()
        async with self.config.guild(ctx.guild).monitored_channels() as monitored_channels:
            monitored_channels.clear()
        async with self.config.guild(ctx.guild).archive_channels() as archive_channels:
            archive_channels.clear()
        await ctx.send("Cleared pin settings/history")

    @checks.admin()
    @pinhistory.group(name="update", invoke_without_command=False)
    async def pinhistory_update(self, ctx):
        """
        Commands related to forcing pin history to be updated. Useful when a new monitor channel is configured
        """
        pass

    @checks.admin()
    @pinhistory_update.group(name="all", invoke_without_command=True)
    async def pinhistory_update_all(self, ctx):
        """
        Updates pin history for all monitored channels
        """
        monitored_channels = await self.config.guild(ctx.guild).monitored_channels()
        for monitored_channel_id in monitored_channels:
            monitored_channel = ctx.guild.get_channel(monitored_channel_id)
            for pin in reversed(await monitored_channel.pins()):
                await self.archive_pin(monitored_channel, pin)
            await self.manage_pins(monitored_channel)
        await ctx.send("Finished pin update")

    @checks.admin()
    @pinhistory.group(name="settings", invoke_without_command=True)
    async def pinhistory_settings(self, ctx):
        """
        Displays current settings and pin history
        """
        # Should display current settings
        settings = await self.config.guild(ctx.guild).get_raw()
        await ctx.send("```{}```".format(str(settings)))

    @checks.admin()
    @pinhistory.group(name="pinlimit", invoke_without_command=True)
    async def pinhistory_pinlimit(self, ctx, new_pin_limit : int):
        """
        Set the limit on how many pins can remain pinned before the oldest will be removed
        """
        async with self.config.guild(ctx.guild).pin_limit() as pin_limit:
            pin_limit = new_pin_limit
            await ctx.send("Set pin limit to {}".format(pin_limit))

    @checks.admin()
    @pinhistory.group(name="managepins", invoke_without_command=True)
    async def pinhistory_managepins(self, ctx):
        """
        Toggle if pin management should be enabled.
        Disabling this will prevent automatic unpinning of pinned messages
        """
        async with self.config.guild(ctx.channel.guild).manage_pins() as manage_pins:
            manage_pins = not manage_pins
            await ctx.send("Set pin management to {}".format(new_value))

#    @checks.admin()
#    @pinhistory.group(name="restore", invoke_without_command=True)
#    async def pinhistory_restore(self, ctx):
#        """
#        Restore pins from pin_history
#        """
#       # https://discordpy.readthedocs.io/en/latest/api.html#discord.MessageType
#        pin_history = await self.config.guild(ctx.guild).pin_history()
#        main_channel = ctx.guild.get_channel(150609044665532416)
#
#        for pin_id in pin_history:
#            pin_message = await main_channel.fetch_message(pin_id)
#            await pin_message.pin()


    @checks.admin()
    @pinhistory.group(name="toggle", invoke_without_command=False)
    async def pinhistory_toggle(self, ctx):
        """
        Commands related to toggling monitored and archived channels
        """
        pass

    @checks.admin()
    @pinhistory_toggle.group(name="monitor", invoke_without_command=True)
    async def pinhistory_toggle_monitor(self, ctx):
        """
        Set channel to monitor for pin changes.
        If no channel mentions are provided, it will default to channel command was used in.
        """
        if ctx.message.channel_mentions == []:
            channels = [ctx.channel]
        else:
            channels = ctx.message.channel_mentions

        async with self.config.guild(ctx.guild).monitored_channels() as monitored_channels:
            for channel in channels:
                if channel.id not in monitored_channels:
                    monitored_channels.append(channel.id)
                    await ctx.send("Enabled monitoring for {}".format(channel.name))
                else:
                    monitored_channels.remove(channel.id)
                    await ctx.send("Disabled monitoring for {}".format(channel.name))

    @checks.admin()
    @pinhistory_toggle.group(name="archive", invoke_without_command=True)
    async def pinhistory_toggle_archive(self, ctx):
        """
        Set channel to archive pinned messages in.
        If no channel mentions are provided, it will default to channel command was used in.
        """
        if ctx.message.channel_mentions == []:
            channels = [ctx.channel]
        else:
            channels = ctx.message.channel_mentions

        async with self.config.guild(ctx.guild).archive_channels() as archive_channels:
            for channel in channels:
                if channel.id not in archive_channels:
                    archive_channels.append(channel.id)
                    await ctx.send("Enabled archiving to {}".format(channel.name))
                else:
                    archive_channels.remove(channel.id)
                    await ctx.send("Disabled archiving for {}".format(channel.name))

    # https://leovoel.github.io/embed-visualizer/
    # https://cog-creators.github.io/discord-embed-sandbox/

    async def create_embed(self, message):
        "Create the correctly formatted embed for pinned messages"
        # Create embed using information from message
        embed_message = discord.Embed()
        embed_message.title = "{} posted".format(message.author.display_name)
        embed_message.description = message.content
        embed_message.timestamp = datetime.replace(message.created_at, tzinfo=timezone.utc)
        embed_message.set_author(name="{}#{}".format(message.author.name, message.author.discriminator), url="https://discord.com/users/{}".format(message.author.id), icon_url=message.author.avatar_url)
        embed_message.set_thumbnail(url=message.author.avatar_url)
        embed_message.add_field(name="Sources", value="{} | [Message]({})".format(message.channel.mention, message.jump_url), inline=False)

        attachment_count = len(message.attachments)
        if attachment_count != 0:
            if attachment_count == 1:
                attachment_text = "attachment"
                # The below will only run with 1 attachment, and only if that attachment is an image
                if not (await self.config.guild(message.guild).reupload_images()):
                    # Check if file is an image
                    if self.is_image(message.attachments[0].filename):
                        embed_message.set_image(url=message.attachments[0].url)
            else:
                attachment_text = "attachments"

            embed_message.set_footer(text="{} {}".format(attachment_count, attachment_text))
        return embed_message

    async def return_attachments(self, message):
        """
        Returns a list of Discord attachments as discord.File objects
        """
        files = []
        for attachment in message.attachments:
            if (await self.config.guild(message.guild).reupload_images()) or not self.is_image(attachment.filename) or len(message.attachments) > 1:
                attachment_bytes = BytesIO(await attachment.read())
                files.append(discord.File(fp=attachment_bytes, filename=attachment.filename))
        return files

    async def archive_pin(self, channel, message):
        """
        Archive a pinned message in a provided channel
        """
        archive_channels = await self.config.guild(channel.guild).archive_channels()
        async with self.config.guild(channel.guild).pin_history() as pin_history:
            if message.id not in pin_history:
                # Get list of attachments from message
                # Save list of attachment objects to a list of file like objects
                # Send embed with provided attachments
                embed_message = await self.create_embed(message)
                for channel_id in archive_channels:
                    files = await self.return_attachments(message)
                    archive_channel = channel.guild.get_channel(channel_id)
                    await archive_channel.send(embed=embed_message, files=files)
                pin_history.append(message.id)

    def is_image(self, filename):
        """
        Returns True if filename is one of the images listed below
        """
        return os.path.splitext(filename)[1].lower() in [".png", ".jpg", ".jpeg", ".gif"]

    async def manage_pins(self, channel):
        """
        Removes pins that are past the pin_limit
        """
        if await self.config.guild(channel.guild).manage_pins():
            pins = await channel.pins()
            pins_len = len(pins)
            pin_limit = await self.config.guild(channel.guild).pin_limit()

            if pins_len > pin_limit: # Do not let code proceed with pins_len == pin_limit. Will delete all pins [0:]
                for pin in pins[pin_limit-pins_len:]:
                    await pin.unpin(reason="Pin clean up")

    # https://discordpy.readthedocs.io/en/latest/api.html#discord.on_guild_channel_pins_update
    # Monitored Events
    @commands.Cog.listener('on_guild_channel_pins_update') # Executes the below command when a channels pinned messages changes
    async def on_pin_update(self, channel, last_pin):
        monitored_channels = await self.config.guild(channel.guild).monitored_channels()
        if (channel.id in monitored_channels) and (last_pin != None):
            # Check if this pin hasn't already been archived
            last_pinned_message = (await channel.pins())[0]
            await self.archive_pin(channel, last_pinned_message)
            await self.manage_pins(channel)

#    @commands.Cog.listener('on_message') # Executes the below command when a channels pinned messages changes
#    async def on_pinned_message(self, message):
#        if message.type == discord.MessageType.pins_add:
#            await message.delete()
