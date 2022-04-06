import discord
from discord import app_commands, Object
from discord.ext import commands
from discord.ext.commands import Greedy, Context

from typing import Optional, Literal


class botCommands(commands.Cog, name="Bot commands"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot





async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(botCommands(bot))