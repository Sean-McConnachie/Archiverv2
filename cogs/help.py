from discord.ext import commands


class HelpCommand(commands.MinimalHelpCommand):
    def get_command_signature(self, command):
        return '{0.clean_prefix}{1.qualified_name} {1.signature}'.format(self, command)


class HelpCog(commands.Cog, name='Help module'):
    def __init__(self, bot):
        self.bot = bot
        self.original_help_command = self.bot.help_command
        self.bot.help_command = HelpCommand()
        self.bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.original_help_command


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
