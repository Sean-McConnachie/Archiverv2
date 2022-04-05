import discord
import datetime as dt
from discord.ext import commands
from simplicity.json_handler import jLoad

from cogs.create.create_from_search import createFromSearch


CONFIG = jLoad('config.json')


class logMsgsCog(commands.Cog, name='Logging module'):
    """
    This class simply inserts all messages sent in active channels (in active categories) to the threads database.
    We must listen for:
        - on_message
        - on_message_edit
        - on_message_delete
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ACTIVE_CATEGORIES = []
        for cat in CONFIG["application"]["server_data"]["active_channels_folder_id"]:
            self.ACTIVE_CATEGORIES.append(cat["category_id"])


    def isActiveCategory(self, message: discord.Message):
        # check if message is from the bot
        if message.author.id == self.bot.user.id:
            return False
        # check if message is in active categories
        if message.channel.category.id not in self.ACTIVE_CATEGORIES:
            return False
        return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.isActiveCategory(message):
            if message.channel.id == CONFIG["application"]["server_data"]["archiver_channel_id"]:
                # this is where we would create the search window
                await createFromSearch(bot=self.bot, message=message)
                return
            else:
                return
        channel_id = message.channel.id
        query = "SELECT topic_id FROM topics WHERE channel_id = $1;"
        topic_id = await self.bot.db.fetchval(query, channel_id)

        message_id = message.id
        sender_id = message.author.id
        dt_sent = dt.datetime.now()
        if CONFIG["user_roles"]["tutor_role_id"] in message.author.roles:
            is_tutor = True
        else:
            is_tutor = False
        message_content = message.content
        file_links = []
        for file in message.attachments:
            file_links.append(file.url)

        query = """
        INSERT INTO threads (
            topic_id,
            message_id,
            sender_id,
            dt_sent,
            is_tutor,
            message_content,
            file_links)
        VALUES (
            $1, $2, $3, $4, $5, $6, $7
        )
        """
        values = (topic_id, message_id, sender_id, dt_sent, is_tutor, message_content, file_links)
        await self.bot.db.execute(query, *values)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        # don't forget to delete files if the message has had a file removed.
        if not self.isActiveCategory(after):
            return

        query = "UPDATE threads SET message_content = $1, file_links = $2 WHERE message_id = $3;"
        file_links = []
        for file in after.attachments:
            file_links.append(file.url)
        values = (after.content, file_links, before.id)
        await self.bot.db.execute(query, *values)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not self.isActiveCategory(message):
            return
        query = "DELETE FROM threads WHERE message_id = $1"
        await self.bot.db.execute(query, message.id)


async def setup(bot):
    await bot.add_cog(logMsgsCog(bot))
