import os
import asyncio
import discord
import datetime as dt

from cogs.embeds.prettyEmbed import prettyEmbed
from HTMLGenerator.generator import make_template
from simplicity.json_handler import jLoad, jWrite_ifnotexists


CONFIG = jLoad('config.json')


async def createFromNew(interaction: discord.Interaction, data: dict):
    new_data = {
        "topic_name": data["topic_name"],
        "channel_name": data["channel_name"],
        "description": data["description"],
        "class_option": data["class_option"],
        "topic_tags": data["topic_tags"],
    }

    # send a message to acknowledge response
    embed = prettyEmbed(
        title="Creating your topic now",
        description="",
        color=0x00FF00,
        creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

    # create channel and send basic info to channel + insert into database
    for roles in CONFIG["class_roles"]:
        if roles["display_name"] == new_data["class_option"]:
            table_name = roles["table_role_name"]
    for category in CONFIG["application"]["server_data"]["active_channels_folder_id"]:
        if category["table_role_name"] == table_name:
            active_category_id = category["category_id"]
    active_category = discord.utils.get(interaction.guild.channels, id=active_category_id)
    if len(active_category.channels) >= 50:
        # too many active topics - remove oldest channel, archive it
        old_channel = active_category.channels[-1]
        query = "UPDATE topics SET dt_closed = $1 WHERE channel_id = $2;"
        await interaction.client.db.execute(query, dt.datetime.now(), old_channel.id)
        embed = prettyEmbed(
            title=f"Deleting the oldest channel",
            description=f"The category is full. Deleting {old_channel.name} to create space for your topic.",
            color=0xFF0000,
            creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
        )
        await interaction.edit_original_message(embed=embed)
        await old_channel.delete(
            reason=f"The category was full. User {interaction.user.id} caused the overflow delete.")

    db_data = {
        "channel_id": None,
        "topic_name": new_data["topic_name"],
        "channel_name": new_data["channel_name"],
        "topic_description": new_data["description"],
        "class_name": new_data["class_option"],
        "topic_tags": new_data["topic_tags"],
        "dt_created": dt.datetime.now(),
        "creator_id": interaction.user.id
    }

    # create the new topic channel
    new_channel = await active_category.create_text_channel(name=db_data["channel_name"])
    db_data['channel_id'] = new_channel.id

    basic_content = f"""
    ***{db_data["class_name"]}***

    {db_data["topic_description"]}

    Tags: *{", ".join(db_data["topic_tags"])}*

    **Upvotes:** {{0}} | **Downvotes:** {{1}}
    """
    upvotes = 0
    downvotes = 0

    content = basic_content.format(upvotes, downvotes)
    embed = prettyEmbed(
        title=data["topic_name"],
        description=content,
        color=0x0000FF,
        author=discord.utils.get(interaction.guild.members, id=db_data["creator_id"])
    )
    view = ActiveChannelView(embed=embed, basic_content=basic_content)

    msg = await new_channel.send(embed=embed, view=view)
    await msg.pin()

    query = """
    INSERT INTO topics (
        channel_id,
        topic_name,
        channel_name,
        topic_description,
        class_name,
        topic_tags,
        dt_created,
        creator_id
    )
    VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8
    )
    """
    await interaction.client.db.execute(query, *tuple(db_data.values()))

    # update original response message with link to new channel
    embed = prettyEmbed(
        title=f"New topic created!",
        description=f"Go to <#{new_channel.id}>",
        color=0x00FF00,
        creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
    )
    await interaction.edit_original_message(embed=embed)


class ActiveChannelView(discord.ui.View):
    def __init__(self, embed: prettyEmbed, basic_content: str):
        super().__init__(timeout=None)
        self.Embed = embed
        self.basic_content = basic_content

    @discord.ui.button(label="Archive this topic", style=discord.ButtonStyle.blurple, emoji=CONFIG["application"]["server_data"]["search_archive_emoji"], custom_id="archive_callback")
    async def archive_callback(self, button: discord.Button, interaction: discord.Interaction):
        query = "SELECT creator_id FROM topics WHERE channel_id = $1;"
        creator_id = await interaction.client.db.fetchval(query, interaction.channel.id)
        if creator_id == interaction.user.id:
            # send modal for confirmation
            modal_view = confirmArchiveModal()
            modal_view.topic_name.placeholder = f"{interaction.channel.name}"
            await interaction.response.send_modal(modal_view)
        else:
            # send error to fake user xd
            embed = prettyEmbed(message_id="not_creator_active",
                                creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Upvote", emoji=CONFIG["application"]["server_data"]["upvote_emoji"], custom_id="upvote_callback")
    async def upvote_callback(self, button: discord.Button, interaction: discord.Interaction):
        query = "SELECT downvotes, upvotes FROM topics WHERE channel_id = $1;"
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
        query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE channel_id = $3"
        await interaction.client.db.execute(query, upvotes, downvotes, interaction.channel.id)
        await self.update_embed(upvotes=upvotes, downvotes=downvotes, interaction=interaction)
        await interaction.response.defer()

    @discord.ui.button(label="Downvote", emoji=CONFIG["application"]["server_data"]["downvote_emoji"], custom_id="downvote_callback")
    async def downvote_callback(self, button: discord.Button, interaction: discord.Interaction):
        query = "SELECT downvotes, upvotes FROM topics WHERE channel_id = $1;"
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
        query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE channel_id = $3"
        await interaction.client.db.execute(query, upvotes, downvotes, interaction.channel.id)
        await self.update_embed(upvotes=upvotes, downvotes=downvotes, interaction=interaction)
        await interaction.response.defer()

    @discord.ui.button(label="Remove vote", emoji=CONFIG["application"]["server_data"]["removevote_emoji"], custom_id="removevote_callback")
    async def removevote_callback(self, button: discord.Button, interaction: discord.Interaction):
        query = "SELECT downvotes, upvotes FROM topics WHERE channel_id = $1;"
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
        query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE channel_id = $3"
        await interaction.client.db.execute(query, upvotes, downvotes, interaction.channel.id)
        await self.update_embed(upvotes=upvotes, downvotes=downvotes, interaction=interaction)
        await interaction.response.defer()

    async def update_embed(self, upvotes: list, downvotes: list, interaction: discord.Interaction):
        temp = self.basic_content
        temp = temp.format(len(upvotes), len(downvotes))
        self.Embed.description = temp
        await interaction.message.edit(embed=self.Embed)


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
