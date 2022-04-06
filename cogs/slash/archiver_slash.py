import discord
from discord import app_commands, Object
from discord.ext import commands
from discord.ext.commands import Greedy, Context

from typing import Optional, Literal

from clients.bot import getUserRoles
from cogs.create.create_from_new import createFromNew
from cogs.create.create_from_search import createFromSearch
from cogs.embeds.prettyEmbed import prettyEmbed
from cogs.embeds.search_embed import searchEmbed
from cogs.modals.validate_modal_inputs import validateModal
from cogs.shared_functions import get_results
from cogs.views.search_view import searchEmbedView


class archiverSlash(commands.Cog, name="Create search slash"):
    """
    /create <topic name> <description> <class (must be known to user)> <tags>

    /search <topic name> <class (optional)> <tags (optional)>

    /open <topic id> <topic name>

    /archive <topic name>

    /upvote

    /downvote

    /removevote
    """
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @app_commands.command(name="create")
    async def create_command(self,
                             interaction: discord.Interaction,
                             name: str,
                             description: str,
                             class_name: str,
                             tags: str) -> None:
        """
        /create <topic name> <description> <class (e.g. COMPSCI 110)> <tags (seperated by comma)>
        """
        # now verify all the data, insert it into the database, create a channel, then send a message in that channel for up/down votes

        data = {
            "topic_name": name,
            "description": description,
            "class_option": class_name,
            "topic_tags": tags
        }

        classes = await getUserRoles(interaction=interaction)

        data = validateModal(data=data, classes=classes)

        if "error" in data.keys():
            embed = prettyEmbed(
                title="oops",
                description=data["error"],
                color=0xFF0000,
                creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await createFromNew(interaction=interaction, data=data)


    @app_commands.command(name="search")
    async def search_command(self,
                             interaction: discord.Interaction,
                             name: str, class_name: Optional[str] = None,
                             tags: Optional[str] = None) -> None:
        """
        /search <topic name> <class (optional)> <tags (optional)>
        """

        data = {
            "topic_name": name,
            "class_option": class_name,
            "topic_tags": tags
        }

        classes = await getUserRoles(interaction=interaction)

        data = validateModal(data=data, classes=classes)

        if "error" in data.keys():
            if "topic_name" in data["error_tags"]:
                embed = prettyEmbed(
                    title="oops",
                    description=data["error"],
                    color=0xFF0000,
                    creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        results = await get_results(data, interaction)
        embed = searchEmbed(data, results)
        view = searchEmbedView(embed=embed)

        await interaction.user.send(content=embed.description, view=view)

        embed = prettyEmbed(
            message_id="check_dms",
            creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="open")
    async def open_command(self, interaction: discord.Interaction,
                             id: int,
                             name: str) -> None:
        """
        /search <topic id> <topic name>
        """

        await createFromSearch(bot=self.bot, interaction=interaction, topic_id=id, topic_name=name)

    @app_commands.command(name="archive")
    async def archive_command(self, interaction: discord.Interaction, name: str) -> None:
        """
        /archive <channel name>   | will archive the topic
        """
        pass

    @app_commands.command(name="upvote")
    async def upvote_command(self, interaction: discord.Interaction) -> None:
        """
        Upvote this topic
        """
        pass

    @app_commands.command(name="downvote")
    async def downvote_command(self, interaction: discord.Interaction) -> None:
        """
        Downvote this topic
        """
        pass

    @app_commands.command(name="removevote")
    async def removevote_command(self, interaction: discord.Interaction) -> None:
        """
        Remove your vote on this topic
        """
        pass

    @commands.command()
    async def sync(self, ctx: Context, guilds: Greedy[Object], spec: Optional[Literal["here"]] = None) -> None:
        await ctx.message.delete()
        """
        sync -> global sync
        sync here -> sync current guild
        sync id_1 id_2 -> syncs guilds with id 1 and 2
        :param ctx:
        :param guilds:
        :param spec:
        :return:
        """
        # this command is only for admins
        query = "SELECT role_id FROM role_data WHERE is_admin = true;"
        is_admin = await ctx.bot.db.fetchval(query)

        if not is_admin:
            return

        if not guilds:
            if spec == "here":
                fmt = await ctx.bot.tree.sync(guild=ctx.guild)
            else:
                fmt = await ctx.bot.tree.sync()

            await ctx.message.author.send(
                f"Synced {len(fmt)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        assert guilds is not None
        fmt = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                fmt += 1

        await ctx.message.author.send(f"Synced the tree to {fmt}/{len(guilds)} guilds.")



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(archiverSlash(bot))