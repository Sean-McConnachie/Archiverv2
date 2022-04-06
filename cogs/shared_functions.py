import discord
from fuzzywuzzy import process
import datetime as dt


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


async def get_results(data:dict , interaction: discord.Interaction) -> list:
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