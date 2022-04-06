import discord
from cogs.embeds.prettyEmbed import prettyEmbed
import datetime as dt

from cogs.shared_functions import delete_channel


class confirmArchiveModal(discord.ui.Modal, title="Are you sure?"):
    topic_name = discord.ui.TextInput(label="Type the channel name to archive the topic", custom_id="channel_name")

    def __init__(self, Active: bool):
        super().__init__()
        self.Active = Active

    async def on_submit(self, interaction: discord.Interaction):
        response = interaction.data
        data = {}
        for i in range(len(response["components"])):
            comp_dict = response["components"][i]["components"][0]
            data[comp_dict["custom_id"]] = comp_dict["value"]

        if data['channel_name'].lower() == interaction.channel.name.lower():
            await delete_channel(interaction=interaction, Active=self.Active)
        else:
            if self.Active:
                embed = prettyEmbed(message_id="wrong_name_archive_on_active",
                                    creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
            else:
                embed = prettyEmbed(
                    message_id="wrong_name_archive_on_archive",
                    creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)