import discord
import numpy as np
from fuzzywuzzy import process

from cogs.embeds.search_embed import searchEmbed
from cogs.modals.validate_modal_inputs import validateModal
from cogs.shared_functions import get_results
from cogs.views.search_view import searchEmbedView
from simplicity.json_handler import jLoad
from cogs.embeds.prettyEmbed import prettyEmbed
import datetime as dt


CONFIG = jLoad('static_files/config.json')
TAGS = jLoad('static_files/tags.json')


class searchModal(discord.ui.Modal, title='Search for a topic'):
    classes = []
    topic_name = discord.ui.TextInput(label="Topic name", custom_id="topic_name")
    class_option = discord.ui.TextInput(label='Class (choose one)', placeholder="Eg. COMPSCI 110", style=discord.TextStyle.short, custom_id="class_option", required=False)
    topic_tags = discord.ui.TextInput(label="Tags (separate with a ,)", custom_id="topic_tags", required=False)


    async def on_submit(self, interaction: discord.Interaction):
        response = interaction.data

        data = {}
        for i in range(len(response["components"])):
            comp_dict = response["components"][i]["components"][0]
            data[comp_dict["custom_id"]] = comp_dict["value"]

        data = validateModal(data=data, classes=self.classes)

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