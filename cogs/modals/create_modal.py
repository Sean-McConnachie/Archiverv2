import string
import discord
import datetime as dt

from cogs.modals.validate_modal_inputs import validateModal
from simplicity.json_handler import jLoad
from cogs.embeds.prettyEmbed import prettyEmbed


from cogs.create.create_from_new import createFromNew


CONFIG = jLoad('static_files/config.json')
TAGS = jLoad('static_files/tags.json')


class createModal(discord.ui.Modal, title='Create a topic'):
    classes = []
    """
    @staticmethod
    def get_category_id_from_role(table_role_name: str) -> str:
        for i in range(len(CONFIG["application"]["server_data"]["active_channels_folder_id"])):
            class_dict = CONFIG["application"]["server_data"]["active_channels_folder_id"][i]
            if class_dict["table_role_name"] == table_role_name:
                return str(class_dict["category_id"])

    class_options = []
    for i in range(len(CONFIG["class_roles"])):
        class_dict = CONFIG["class_roles"][i]
        class_options.append(
            discord.SelectOption(
                label=class_dict["display_name"],
                value=get_category_id_from_role(class_dict["table_role_name"])
            )
        )
    """

    topic_name = discord.ui.TextInput(label="Topic name", custom_id="topic_name")
    description = discord.ui.TextInput(label='Description', style=discord.TextStyle.paragraph, custom_id="description")
    class_option = discord.ui.TextInput(label='Class (choose one)', placeholder="Eg. COMPSCI 110",
                                        style=discord.TextStyle.short, custom_id="class_option")
    # class_options = discord.ui.Select(placeholder="Select class", options=class_options, min_values=1, max_values=1) # TODO: Add dropdown support once it is provided
    topic_tags = discord.ui.TextInput(label="Tags (separate with a ,)", custom_id="topic_tags")

    async def on_submit(self, interaction: discord.Interaction):
        response = interaction.data
        data = {}
        for i in range(len(response["components"])):
            comp_dict = response["components"][i]["components"][0]
            data[comp_dict["custom_id"]] = comp_dict["value"]

        # now verify all the data, insert it into the database, create a channel, then send a message in that channel for up/down votes
        data = validateModal(data=data, classes=self.classes)

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

