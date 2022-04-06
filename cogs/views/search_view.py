import discord

from cogs.embeds.search_embed import searchEmbed


class searchEmbedView(discord.ui.View):
    def __init__(self, embed: searchEmbed):
        super().__init__(timeout=None)
        self.Embed = embed

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="❌", custom_id="close_embed")
    async def close_embed(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.message.delete()
        await interaction.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji='⬅️', custom_id="previous_page")
    async def previous_page(self, interaction: discord.Interaction, button: discord.Button):
        self.Embed.previous_page()
        await interaction.message.edit(content=self.Embed.description)
        await interaction.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="➡️", custom_id="next_page")
    async def next_page(self, interaction: discord.Interaction, button: discord.Button):
        self.Embed.next_page()
        await interaction.message.edit(content=self.Embed.description)
        await interaction.response.defer()

    @discord.ui.button(label="Relevance", style=discord.ButtonStyle.secondary, custom_id="relevance_callback")
    async def relevance_callback(self, interaction: discord.Interaction, button: discord.Button):
        self.Embed.relevanceSort()
        await interaction.message.edit(content=self.Embed.description)
        await interaction.response.defer()

    @discord.ui.button(label="Upvotes", style=discord.ButtonStyle.secondary, custom_id="upvotes_callback")
    async def upvotes_callback(self, interaction: discord.Interaction, button: discord.Button):
        self.Embed.upvotesSort()
        await interaction.message.edit(content=self.Embed.description)
        await interaction.response.defer()
