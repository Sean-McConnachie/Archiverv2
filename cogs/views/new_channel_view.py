import discord
from cogs.embeds.prettyEmbed import prettyEmbed
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
            modal_view = confirmArchiveModal()
            modal_view.topic_name.placeholder = f"{interaction.channel.name}"
            await interaction.response.send_modal(modal_view)
        else:
            # send error to fake user xd
            embed = prettyEmbed(message_id="not_creator_archive",
                                creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Upvote", emoji=CONFIG["server_data"]["upvote_emoji"], custom_id="upvote_callback")
    async def upvote_callback(self, interaction: discord.Interaction, button: discord.Button):
        if self.Active:
            query = "SELECT downvotes, upvotes FROM topics WHERE channel_id = $1;"
        else:
            query = "SELECT downvotes, upvotes FROM topics WHERE archive_channel_id = $1;"
        record = await interaction.client.db.fetch(query, interaction.channel.id)
        record = record[0]
        downvotes = record["downvotes"]
        upvotes = record["upvotes"]
        if downvotes is None:
            downvotes = []
        if upvotes is None:
            upvotes = []
        if interaction.user.id in downvotes:
            downvotes.remove(interaction.user.id)
        if interaction.user.id in upvotes:
            pass
        if interaction.user.id not in upvotes:
            upvotes.append(interaction.user.id)

        if self.Active:
            query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE channel_id = $3"
        else:
            query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE archive_channel_id = $3"
        await interaction.client.db.execute(query, upvotes, downvotes, interaction.channel.id)
        await self.update_embed(upvotes=upvotes, downvotes=downvotes, interaction=interaction)
        await interaction.response.defer()

    @discord.ui.button(label="Downvote", emoji=CONFIG["server_data"]["downvote_emoji"], custom_id="downvote_callback")
    async def downvote_callback(self, interaction: discord.Interaction, button: discord.Button):
        if self.Active:
            query = "SELECT downvotes, upvotes FROM topics WHERE channel_id = $1;"
        else:
            query = "SELECT downvotes, upvotes FROM topics WHERE archive_channel_id = $1;"
        record = await interaction.client.db.fetch(query, interaction.channel.id)
        record = record[0]
        downvotes = record["downvotes"]
        upvotes = record["upvotes"]
        if downvotes is None:
            downvotes = []
        if upvotes is None:
            upvotes = []
        if interaction.user.id in upvotes:
            upvotes.remove(interaction.user.id)
        if interaction.user.id in downvotes:
            pass
        if interaction.user.id not in downvotes:
            downvotes.append(interaction.user.id)

        if self.Active:
            query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE channel_id = $3"
        else:
            query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE archive_channel_id = $3"
        await interaction.client.db.execute(query, upvotes, downvotes, interaction.channel.id)
        await self.update_embed(upvotes=upvotes, downvotes=downvotes, interaction=interaction)
        await interaction.response.defer()

    @discord.ui.button(label="Remove vote", emoji=CONFIG["server_data"]["removevote_emoji"], custom_id="removevote_callback")
    async def removevote_callback(self, interaction: discord.Interaction, button: discord.Button):
        if self.Active:
            query = "SELECT downvotes, upvotes FROM topics WHERE channel_id = $1;"
        else:
            query = "SELECT downvotes, upvotes FROM topics WHERE archive_channel_id = $1;"
        record = await interaction.client.db.fetch(query, interaction.channel.id)
        record = record[0]
        downvotes = record["downvotes"]
        upvotes = record["upvotes"]
        if downvotes is None:
            downvotes = []
        if upvotes is None:
            upvotes = []
        if interaction.user.id in upvotes:
            upvotes.remove(interaction.user.id)
        if interaction.user.id in downvotes:
            downvotes.remove(interaction.user.id)

        if self.Active:
            query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE channel_id = $3"
        else:
            query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE archive_channel_id = $3"
        await interaction.client.db.execute(query, upvotes, downvotes, interaction.channel.id)
        await self.update_embed(upvotes=upvotes, downvotes=downvotes, interaction=interaction)
        await interaction.response.defer()

    async def update_embed(self, upvotes: list, downvotes: list, interaction: discord.Interaction):
        temp = self.basic_content
        temp = temp.format(len(upvotes), len(downvotes))
        self.Embed.description = temp
        await interaction.message.edit(embed=self.Embed)