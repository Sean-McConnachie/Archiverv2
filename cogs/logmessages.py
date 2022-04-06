import discord
import datetime as dt
from discord.ext import commands

from cogs.shared_functions import isActiveCategory
from simplicity.json_handler import jLoad

from cogs.create.create_from_search import createFromSearch


CONFIG = jLoad('static_files/config.json')


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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content.startswith(CONFIG["application"]["prefix"]):
            return
        if not await isActiveCategory(bot=self.bot, message=message):
            return
        channel_id = message.channel.id
        query = "SELECT topic_id FROM topics WHERE channel_id = $1;"
        topic_id = await self.bot.db.fetchval(query, channel_id)

        message_id = message.id
        sender_id = message.author.id
        dt_sent = dt.datetime.now()

        # check if user is a tutor and set is_tutor accordingly

        query = "SELECT role_id FROM role_data WHERE is_tutor = $1"
        resp = await self.bot.db.fetch(query, True)

        is_tutor = False
        author_roles = [i.id for i in message.author.roles]
        for r in resp:
            role_id = r[0]
            if role_id in author_roles:
                is_tutor = True

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
        if not await isActiveCategory(bot=self.bot, message=after):
            return

        query = "UPDATE threads SET message_content = $1, file_links = $2 WHERE message_id = $3;"
        file_links = []
        for file in after.attachments:
            file_links.append(file.url)
        values = (after.content, file_links, before.id)
        await self.bot.db.execute(query, *values)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not await isActiveCategory(bot=self.bot, message=message):
            return
        query = "DELETE FROM threads WHERE message_id = $1"
        await self.bot.db.execute(query, message.id)


async def setup(bot):
    await bot.add_cog(logMsgsCog(bot))
