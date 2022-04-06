import discord
from cogs.embeds.prettyEmbed import prettyEmbed
import datetime as dt


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

        if self.Active:
            if data['channel_name'].lower() == interaction.channel.name.lower():
                # they have successfully confirmed deletion
                embed = prettyEmbed(message_id="confirm_archive_on_active",
                                    creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
                await interaction.response.send_message(embed=embed, ephemeral=True)
                query = "UPDATE topics SET channel_id=$1, dt_closed = $2, currently_open = $3 WHERE channel_id = $4;"
                await interaction.client.db.execute(query, None, dt.datetime.now(), False, interaction.channel.id)
                await interaction.channel.delete(reason=f"{interaction.user.id} archived the post.")
            else:
                embed = prettyEmbed(message_id="wrong_name_archive_on_active",
                                    creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            if data['channel_name'].lower() == interaction.channel.name.lower():
                # they have successfully confirmed deletion
                embed = prettyEmbed(message_id="confirm_archive_on_archive",
                                    creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
                await interaction.response.send_message(embed=embed, ephemeral=True)
                query = "UPDATE topics SET archive_channel_id = $1, archive_dt_close = $2, archive_creator_id = $3, currently_open = $4 WHERE archive_channel_id = $5;"
                await interaction.client.db.execute(query, None, dt.datetime.now(), None, False, interaction.channel.id)
                await interaction.channel.delete(reason=f"{interaction.user.id} archived the post.")
            else:
                embed = prettyEmbed(
                    message_id="wrong_name_archive_on_archive",
                    creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)