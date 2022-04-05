import os
import asyncio
import discord
import datetime as dt

from cogs.embeds.prettyEmbed import prettyEmbed
from simplicity.json_handler import jLoad
from cogs.views.new_channel_view import newChannelView


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
        author=discord.utils.get(interaction.guild.members, id=db_data["creator_id"]),
        creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
    )
    view = newChannelView(embed=embed, basic_content=basic_content)

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


