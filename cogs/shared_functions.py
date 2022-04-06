import discord
from fuzzywuzzy import process
import datetime as dt

from cogs.embeds.prettyEmbed import prettyEmbed


async def up_down_vote(interaction: discord.Interaction, vote: str) -> dict or None:
    Active = await simpleIsActiveCategory(interaction=interaction)
    if Active is None:
        embed = prettyEmbed(
            title="Sorry mate",
            description=f"This isn't a valid channel",
            color=0xFF0000,
            creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return None

    if Active:
        query = "SELECT downvotes, upvotes, topic_id, dt_closed FROM topics WHERE channel_id = $1;"
    else:
        query = "SELECT downvotes, upvotes, topic_id, archive_dt_close FROM topics WHERE archive_channel_id = $1;"

    record = await interaction.client.db.fetch(query, interaction.channel.id)
    record = record[0]
    downvotes = record["downvotes"]
    upvotes = record["upvotes"]
    if downvotes is None:
        downvotes = []
    if upvotes is None:
        upvotes = []

    if vote == "up":
        if interaction.user.id in downvotes:
            downvotes.remove(interaction.user.id)
        if interaction.user.id in upvotes:
            pass
        if interaction.user.id not in upvotes:
            upvotes.append(interaction.user.id)
    elif vote == "down":
        if interaction.user.id in upvotes:
            upvotes.remove(interaction.user.id)
        if interaction.user.id in downvotes:
            pass
        if interaction.user.id not in downvotes:
            downvotes.append(interaction.user.id)
    elif vote == "remove":
        if interaction.user.id in upvotes:
            upvotes.remove(interaction.user.id)
        if interaction.user.id in downvotes:
            downvotes.remove(interaction.user.id)
    elif vote == "none":
        pass

    if Active:
        query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE channel_id = $3"
    else:
        query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE archive_channel_id = $3"
    await interaction.client.db.execute(query, upvotes, downvotes, interaction.channel.id)

    if vote != "none":
        content = f"""```yaml
Upvotes {len(upvotes)}
``````fix
Downvotes {len(downvotes)}
```"""
    else:
        content = """```yaml
The interactions should be working again.
```"""
    await interaction.response.send_message(content=content, ephemeral=True)

    return {
        "upvotes": upvotes,
        "downvotes": downvotes,
        "interaction": interaction,
        "topic_id": record["topic_id"],
        "dt_closed": record["dt_closed"] if Active else record["archive_dt_close"]
    }


async def delete_channel(interaction: discord.Interaction, Active: bool):
    if Active:
        # they have successfully confirmed deletion
        embed = prettyEmbed(message_id="confirm_archive_on_active",
                            creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
        await interaction.response.send_message(embed=embed, ephemeral=True)
        query = "UPDATE topics SET channel_id=$1, dt_closed = $2, currently_open = $3 WHERE channel_id = $4;"
        await interaction.client.db.execute(query, None, dt.datetime.now(), False, interaction.channel.id)
        await interaction.channel.delete(reason=f"{interaction.user.id} archived the post.")
    else:
        # they have successfully confirmed deletion
        embed = prettyEmbed(message_id="confirm_archive_on_archive",
                            creator=discord.utils.get(interaction.guild.members, id=355832318532780062))
        await interaction.response.send_message(embed=embed, ephemeral=True)
        query = "UPDATE topics SET archive_channel_id = $1, archive_dt_close = $2, archive_creator_id = $3, " \
                "currently_open = $4 WHERE archive_channel_id = $5; "
        await interaction.client.db.execute(query, None, dt.datetime.now(), None, False, interaction.channel.id)
        await interaction.channel.delete(reason=f"{interaction.user.id} archived the post.")


async def simpleIsActiveCategory(interaction: discord.Interaction):
    """
    :param interaction:
    :return: Active; True if active category, False if Archive category, None if neither
    """
    # check if message is from the bot
    query = "SELECT topic_id FROM topics WHERE channel_id = $1"
    Active_id = await interaction.client.db.fetchval(query, interaction.channel.id)

    query = "SELECT topic_id FROM topics WHERE archive_channel_id = $1"
    Archive_id = await interaction.client.db.fetchval(query, interaction.channel.id)

    if Active_id is None and Archive_id is None:
        return None
    elif Active_id is not None:
        return True
    elif Archive_id is not None:
        return False


async def isActiveCategory(bot,
                           message: discord.Message = None,
                           interaction: discord.Interaction = None):
    # check if message is from the bot
    if message is not None:
        if message.author.id == bot.user.id:
            return False
    else:
        if interaction.user.id == bot.user.id:
            return False

    # check if message is a DM
    if interaction is not None:
        message = interaction
    if isinstance(message.channel, discord.DMChannel):
        return False

    # check if message is in active categories
    query = "SELECT active_category FROM category_data WHERE category_id = $1"
    resp = await bot.db.fetchval(query, message.channel.category.id)

    if resp is False:
        return False
    elif resp is None:
        return False
    else:
        return True


async def getUserRoles(interaction: discord.Interaction):
    useable = []
    # this gets all of the user's roles, then checks what CLASSES (i.e. not tutor or admin) the person is in.
    roles = {}
    for role in interaction.user.roles:
        roles[role.id] = role.name

    query = "SELECT role_id FROM role_data WHERE is_class = true;"
    resp = await interaction.client.db.fetch(query)

    class_roles = [i[0] for i in resp]
    for role_id in roles:
        if role_id in class_roles:
            useable.append(roles[role_id])
    return useable


async def get_results(data: dict, interaction: discord.Interaction) -> list:
    resp = []

    if "class_option" not in data.keys():
        data["class_option"] = None
    if "topic_tags" not in data.keys():
        data["topic_tags"] = None

    if data["class_option"] is None and data["topic_tags"] is None:
        query = "SELECT topic_id, topic_name, topic_tags, upvotes, downvotes FROM topics WHERE dt_closed < $1;"
        resp = await interaction.client.db.fetch(query, dt.datetime.now())
    elif data["class_option"] is not None and data["topic_tags"] is not None:
        query = "SELECT topic_id, topic_name, topic_tags, upvotes, downvotes FROM topics WHERE class_name = $1 AND topic_tags @> $2 AND dt_closed < $3"
        resp = await interaction.client.db.fetch(query, data["class_option"], data["topic_tags"], dt.datetime.now())
    elif data["class_option"] is not None:
        query = "SELECT topic_id, topic_name, topic_tags, upvotes, downvotes FROM topics WHERE class_name = $1 AND dt_closed < $2"
        resp = await interaction.client.db.fetch(query, data["class_option"], dt.datetime.now())
    elif data["topic_tags"] is not None:
        query = "SELECT topic_id, topic_name, topic_tags, upvotes, downvotes FROM topics WHERE topic_tags @> $1 AND dt_closed < $2"
        resp = await interaction.client.db.fetch(query, data["topic_tags"], dt.datetime.now())

    temp_results = {}
    tags_dict = {}
    for i in resp:
        temp_results[i["topic_id"]] = i["topic_name"]
        tags_dict[i["topic_id"]] = {"topic_tags": i["topic_tags"],
                                    "upvotes": i["upvotes"],
                                    "downvotes": i["downvotes"]}

    similarities = process.extract(data["topic_name"], temp_results)

    results = []
    for similar in similarities:
        if similar[1] < 30:
            continue
        temp = {
            "topic_name": similar[0],
            "topic_id": similar[2],
            "topic_tags": tags_dict[similar[2]]["topic_tags"],
            "upvotes": tags_dict[similar[2]]["upvotes"],
            "downvotes": tags_dict[similar[2]]["downvotes"]
        }
        if temp["upvotes"] is None:
            temp["upvotes"] = []
        if temp["downvotes"] is None:
            temp["downvotes"] = []
        temp["upvotes"] = len(temp["upvotes"])
        temp["downvotes"] = len(temp["downvotes"])
        temp["votes_total"] = temp["upvotes"] - temp["downvotes"]
        results.append(temp)

    return results
