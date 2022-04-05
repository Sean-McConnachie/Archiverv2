import discord
from cogs.embeds.prettyEmbed import prettyEmbed


class confirmOldArchiveModal(discord.ui.Modal, title="Are you sure?"):
    topic_name = discord.ui.TextInput(label="Type the channel name to archive this topic", custom_id="channel_name")

    async def on_submit(self, interaction: discord.Interaction):
        response = interaction.data
        data = {}
        for i in range(len(response["components"])):
            comp_dict = response["components"][i]["components"][0]
            data[comp_dict["custom_id"]] = comp_dict["value"]
        if data['channel_name'].lower() == interaction.channel.name.lower():
            # they have successfully confirmed deletion
            embed = prettyEmbed(message_id="confirm_archive_on_archive",
                creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
            await interaction.response.send_message(embed=embed, ephemeral=True)
            query = "UPDATE topics SET archive_channel_id = $1, archive_dt_created = $2, archive_creator_id = $3 WHERE archive_channel_id = $4;"
            await interaction.client.db.execute(query, None, None, None, interaction.channel.id)
            await interaction.channel.delete(reason=f"{interaction.user.id} archived the post.")
        else:
            embed = prettyEmbed(
                message_id="wrong_name_archive_on_archive",
                creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

# TODO: these two functions are different but only confirmArchiveModal is called from new_channel_view.py


class confirmArchiveModal(discord.ui.Modal, title="Are you sure?"):
    topic_name = discord.ui.TextInput(label="Type the channel name to archive the topic", custom_id="channel_name")

    async def on_submit(self, interaction: discord.Interaction):
        response = interaction.data
        data = {}
        for i in range(len(response["components"])):
            comp_dict = response["components"][i]["components"][0]
            data[comp_dict["custom_id"]] = comp_dict["value"]
        if data['channel_name'].lower() == interaction.channel.name.lower():
            # they have successfully confirmed deletion
            embed = prettyEmbed(message_id="confirm_archive_on_active",
                                creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
            await interaction.response.send_message(embed=embed, ephemeral=True)
            query = "UPDATE topics SET dt_closed = $1 WHERE channel_id = $2;"
            await interaction.client.db.execute(query, dt.datetime.now(), interaction.channel.id)
            await interaction.channel.delete(reason=f"{interaction.user.id} archived the post.")
        else:
            embed = prettyEmbed(message_id="wrong_name_archive_on_active",
                                creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
            await interaction.response.send_message(embed=embed, ephemeral=True)
