import os
import asyncio

import asyncpg
import discord
from simplicity.json_handler import jLoad
from clients.bot import CustomClient

# TODO: create auto delete
# TODO: create command line version i.e. !create topic_name topic_description etc
# TODO: note that ephemeral messages can be sent to app commands

# import config
CONFIG = jLoad('static_files/config.json')


async def run_bot():
    intents = discord.Intents.all()

    db = await asyncpg.create_pool(**CONFIG["db"])

    bot = CustomClient(
        command_prefix=CONFIG["application"]["prefix"],
        intents=intents,
        db=db,
    )

    for extension in CONFIG["application"]["cogs"]:
        await bot.load_extension(extension)

    await bot.start(CONFIG["application"]["token"])


if __name__ == '__main__':
    if not os.path.exists("temp_files"):
        os.mkdir("temp_files")

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run_bot())
