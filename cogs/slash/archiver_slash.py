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
from cogs.shared_functions import get_results, delete_channel, simpleIsActiveCategory, up_down_vote
from cogs.views.new_channel_view import newChannelView
from cogs.views.search_view import searchEmbedView
import datetime as dt


class archiverSlash(commands.Cog, name="Create search slash"):
    """
    /create <topic name> <description> <class (must be known to user)> <tags>

    /search <topic name> <class (optional)> <tags (optional)>

    /open <topic id> <topic name>

    /archive <topic name>

    /upvote

    /downvote

    /removevote

    /resetinteraction
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
        # this function first checks if they inputted the correct channel name
        # if yes, then check if the channel is in an active or archive category
        # it then checks if the user is the original creator of the channel
        # then call delete_channel

        Active = await simpleIsActiveCategory(interaction=interaction)
        if Active is None:
            return

        if Active:
            query = "SELECT creator_id FROM topics WHERE channel_id = $1;"
        else:
            query = "SELECT archive_creator_id FROM topics WHERE archive_channel_id = $1;"
        creator_id = await interaction.client.db.fetchval(query, interaction.channel.id)

        if not creator_id == interaction.user.id:
            # send error to fake user xd
            embed = prettyEmbed(message_id="not_creator_archive",
                                creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if name.lower() == interaction.channel.name.lower() and creator_id == interaction.user.id:
            await delete_channel(interaction=interaction, Active=Active)
        else:
            if Active:
                embed = prettyEmbed(message_id="wrong_name_archive_on_active",
                                    creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
            else:
                embed = prettyEmbed(
                    message_id="wrong_name_archive_on_archive",
                    creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)


    async def editOrignalMessage(self, interaction: discord.Interaction, new_votes: dict = None):
        original_message = []
        async for message in interaction.channel.history(limit=1, oldest_first=True):
            original_message.append(message)
        original_message = original_message[0]

        query = "SELECT class_name, topic_description, topic_tags, creator_id, topic_name FROM topics WHERE topic_id = $1"
        resp = await interaction.client.db.fetch(query, new_votes["topic_id"])
        resp = resp[0]

        basic_content = f"""
                                ***{resp["class_name"]}***

                                {resp["topic_description"]}

                                Tags: *{", ".join(resp["topic_tags"])}*

                                Closes at: *{new_votes['dt_closed'].strftime("%H:%M %d/%m/%Y")}*

                                **Upvotes:** {{0}} | **Downvotes:** {{1}}
                                """

        content = basic_content.format(len(new_votes["upvotes"]), len(new_votes["downvotes"]))
        embed = prettyEmbed(
            title=resp["topic_name"],
            description=content,
            color=0x0000FF,
            author=discord.utils.get(interaction.guild.members, id=resp["creator_id"]),
            creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
        )
        view = newChannelView(embed=embed, basic_content=basic_content, Active=False)
        await original_message.edit(embed=embed, view=view)


    @app_commands.command(name="upvote")
    async def upvote_command(self, interaction: discord.Interaction) -> None:
        """
        Upvote this topic
        """
        new_votes = await up_down_vote(interaction=interaction, vote="up")
        if new_votes is None:
            return
        await self.editOrignalMessage(interaction=interaction,
                                      new_votes=new_votes)


    @app_commands.command(name="downvote")
    async def downvote_command(self, interaction: discord.Interaction) -> None:
        """
        Downvote this topic
        """
        new_votes = await up_down_vote(interaction=interaction, vote="down")
        if new_votes is None:
            return
        await self.editOrignalMessage(interaction=interaction,
                                      new_votes=new_votes)

    @app_commands.command(name="removevote")
    async def removevote_command(self, interaction: discord.Interaction) -> None:
        """
        Remove your vote on this topic
        """
        new_votes = await up_down_vote(interaction=interaction, vote="remove")
        if new_votes is None:
            return
        await self.editOrignalMessage(interaction=interaction,
                                      new_votes=new_votes)

    @app_commands.command(name="resetinteraction")
    async def reset_command(self, interaction: discord.Interaction) -> None:
        """
        User can call this if the interaction fails to resend it
        :param interaction:
        :return:
        """
        new_votes = await up_down_vote(interaction=interaction, vote="none")
        if new_votes is None:
            return
        await self.editOrignalMessage(interaction=interaction, new_votes=new_votes)

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