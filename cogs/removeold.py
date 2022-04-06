import asyncio

import discord
from discord.ext import tasks, commands

import datetime as dt

from simplicity.json_handler import jLoad

CONFIG = jLoad('static_files/config.json')


class removeOld(commands.Cog, name='Remove old channels'):
    """
    This cog simply removes channels that have surpasses the time they're meant to be closed.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.runLoop.start()

    @tasks.loop(seconds=10)
    async def runLoop(self):
        guild = discord.utils.get(self.bot.guilds, id=CONFIG["server_data"]["guild_id"])

        query = """SELECT topic_id, channel_id FROM topics
        WHERE currently_open = true AND channel_id IS NOT NULL AND dt_closed < $1;"""
        response = await self.bot.db.fetch(query, dt.datetime.now())

        for channel in response:
            try:
                discord_channel = discord.utils.get(guild.channels, id=channel["channel_id"])
                if discord_channel is not None:
                    await discord_channel.delete(reason="This channel has exceeded it's open time.")

                query = "UPDATE topics SET channel_id=$1, dt_closed = $2, currently_open = $3 WHERE topic_id = $4;"
                await self.bot.db.execute(query, None, dt.datetime.now(), False, channel["topic_id"])
            except Exception as e:
                print("Failed to delete message: ", e)


        query = """SELECT topic_id, archive_channel_id FROM topics
        WHERE currently_open = true AND archive_channel_id IS NOT NULL AND archive_dt_close < $1;"""
        response = await self.bot.db.fetch(query, dt.datetime.now())

        for channel in response:
            try:
                discord_channel = discord.utils.get(guild.channels, id=channel["archive_channel_id"])
                if discord_channel is not None:
                    await discord_channel.delete(reason="This channel has exceeded it's open time.")

                query = """UPDATE topics
                SET archive_channel_id = $1, archive_dt_close = $2, archive_creator_id = $3, currently_open = $4
                WHERE topic_id = $5;"""
                await self.bot.db.execute(query, None, dt.datetime.now(), None, False, channel["topic_id"])
            except Exception as e:
                print("Failed to delete message: ", e)



    @runLoop.before_loop
    async def before_runLoop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(1)

async def setup(bot):
    await bot.add_cog(removeOld(bot))
