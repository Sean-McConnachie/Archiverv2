import discord
from cogs.embeds.prettyEmbed import prettyEmbed
from cogs.shared_functions import up_down_vote
from simplicity.json_handler import jLoad
from cogs.modals.channel_delete import confirmArchiveModal


CONFIG = jLoad('static_files/config.json')


class newChannelView(discord.ui.View):
    def __init__(self, embed: prettyEmbed, basic_content: str, Active: bool):
        super().__init__(timeout=None)
        self.Embed = embed
        self.basic_content = basic_content
        self.Active: bool = Active

    @discord.ui.button(label="Archive this topic", style=discord.ButtonStyle.blurple, emoji=CONFIG["server_data"]["search_archive_emoji"], custom_id="archive_callback")
    async def archive_callback(self, interaction: discord.Interaction, button: discord.Button):
        if self.Active:
            query = "SELECT creator_id FROM topics WHERE channel_id = $1;"
        else:
            query = "SELECT archive_creator_id FROM topics WHERE archive_channel_id = $1;"
        creator_id = await interaction.client.db.fetchval(query, interaction.channel.id)
        if creator_id == interaction.user.id:
            # send modal for confirmation
            modal_view = confirmArchiveModal(Active=self.Active)
            modal_view.topic_name.placeholder = f"{interaction.channel.name}"
            await interaction.response.send_modal(modal_view)
        else:
            # send error to fake user xd
            embed = prettyEmbed(message_id="not_creator_archive",
                                creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Upvote", emoji=CONFIG["server_data"]["upvote_emoji"], custom_id="upvote_callback")
    async def upvote_callback(self, interaction: discord.Interaction, button: discord.Button):
        new_votes = await up_down_vote(interaction=interaction, vote="up")
        await self.update_embed(upvotes=new_votes["upvotes"],
                                downvotes=new_votes["downvotes"],
                                interaction=interaction)

    @discord.ui.button(label="Downvote", emoji=CONFIG["server_data"]["downvote_emoji"], custom_id="downvote_callback")
    async def downvote_callback(self, interaction: discord.Interaction, button: discord.Button):
        new_votes = await up_down_vote(interaction=interaction, vote="down")
        await self.update_embed(upvotes=new_votes["upvotes"],
                                downvotes=new_votes["downvotes"],
                                interaction=interaction)

    @discord.ui.button(label="Remove vote", emoji=CONFIG["server_data"]["removevote_emoji"], custom_id="removevote_callback")
    async def removevote_callback(self, interaction: discord.Interaction, button: discord.Button):
        new_votes = await up_down_vote(interaction=interaction, vote="remove")
        await self.update_embed(upvotes=new_votes["upvotes"],
                                downvotes=new_votes["downvotes"],
                                interaction=interaction)

    async def update_embed(self, upvotes: list, downvotes: list, interaction: discord.Interaction):
        temp = self.basic_content
        temp = temp.format(len(upvotes), len(downvotes))
        self.Embed.description = temp
        await interaction.message.edit(embed=self.Embed)