import string
import discord
import datetime as dt
from fuzzywuzzy import process
from json_handler import jLoad
from cogs.prettyEmbed import prettyEmbed


CONFIG = jLoad('config.json')
TAGS = jLoad('tags.json')


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


class createModal(discord.ui.Modal, title='Create a topic'):
    classes = []
    """
    @staticmethod
    def get_category_id_from_role(table_role_name: str) -> str:
        for i in range(len(CONFIG["application"]["server_data"]["active_channels_folder_id"])):
            class_dict = CONFIG["application"]["server_data"]["active_channels_folder_id"][i]
            if class_dict["table_role_name"] == table_role_name:
                return str(class_dict["category_id"])

    class_options = []
    for i in range(len(CONFIG["class_roles"])):
        class_dict = CONFIG["class_roles"][i]
        class_options.append(
            discord.SelectOption(
                label=class_dict["display_name"],
                value=get_category_id_from_role(class_dict["table_role_name"])
            )
        )
    """

    topic_name = discord.ui.TextInput(label="Topic name", custom_id="topic_name")
    description = discord.ui.TextInput(label='Description', style=discord.TextStyle.paragraph, custom_id="description")
    class_option = discord.ui.TextInput(label='Class (choose one)', placeholder="Eg. COMPSCI 110",
                                        style=discord.TextStyle.short, custom_id="class_option")
    # class_options = discord.ui.Select(placeholder="Select class", options=class_options, min_values=1, max_values=1) # TODO: Add dropdown support once it is provided
    topic_tags = discord.ui.TextInput(label="Tags (separate with a ,)", custom_id="topic_tags")

    async def on_submit(self, interaction: discord.Interaction):
        response = interaction.data
        data = {}
        for i in range(len(response["components"])):
            comp_dict = response["components"][i]["components"][0]
            data[comp_dict["custom_id"]] = comp_dict["value"]

        # now verify all the data, insert it into the database, create a channel, then send a message in that channel for up/down votes

        # topic_name, description, class_option, topic_tags
        overall_error = False
        errors = {
            "topic_name": False,
            "description": False,
            "class_option": False,
            "topic_tags": False
        }
        # verify topic_name
        tname_resp = self.cleanTopic(data['topic_name'])
        errors["topic_name"] = tname_resp["error"]
        # verify class_option
        coption_resp = self.verifyClass(data['class_option'])
        errors["class_option"] = coption_resp["error"]
        # verify topic_tags
        ttag_resp = self.cleanTags(data['topic_tags'])
        errors["topic_tags"] = ttag_resp["error"]

        error_in = "You inputted bad data into these field(s):\n"
        for key in errors.keys():
            value = errors[key]
            if value is True:
                overall_error = True
                if key == "topic_name":
                    error_in += " **- Topic name**\n"
                elif key == "description":
                    error_in += " **- Description**\n"
                elif key == "class_option":
                    error_in += " **- Class option**\n"
                elif key == "topic_tags":
                    error_in += " **- Topic tags**\n"
        error_in += "\nPlease look above for more info on valid inputs."

        if overall_error:
            embed = prettyEmbed(
                title="oops",
                description=error_in,
                color=0xFF0000,
                creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        new_data = {
            "topic_name": tname_resp["topic_name"],
            "channel_name": tname_resp["channel_name"],
            "description": data["description"],
            "class_option": coption_resp["class_option"],
            "topic_tags": ttag_resp["topic_tags"],
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
            await old_channel.delete(reason=f"The category was full. User {interaction.user.id} caused the overflow delete.")

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

    def cleanTopic(self, name: str) -> dict:
        error = False

        # remove doulbe whitespaces
        name = ' '.join(name.split())
        # remove double hyphens
        temp = ""
        for i in range(len(name)):
            char = name[i]
            if i == 0:
                temp += char
                continue
            previous = name[i - 1]
            if  (char == "-" and previous == "-") or \
                (char == "-" and previous == " ") or \
                (char == " " and previous == "-") or \
                (char == " " and previous == " "):
                continue
            temp += char
        name = temp

        # remove anything but letters, single hyphens, forward/backslashes and apostrophes + double quotes
        keep = ['-', '/', '\\', "'", '"', ' ']
        keep += string.ascii_letters
        clean = ""
        for i in range(len(name)):
            char = name[i]
            if (i == 0 and char not in string.ascii_letters) or (
                    i == len(name) - 1 and char not in string.ascii_letters):
                continue
            if char in keep:
                clean += char

        # remove trailing special characters
        for i in range(len(clean)):
            char = clean[len(clean) - 1 - i]
            if char in string.ascii_letters:
                clean = clean[0:len(clean) - i]
                break

        if len(clean) <= 1 or len(clean) >= 45:
            error = True

        channel_name = ""
        for char in clean:
            if char in string.ascii_letters:
                channel_name += char
            else:
                channel_name += '-'

        return {
            "topic_name": clean,
            "channel_name": channel_name,
            "error": error
        }

    def verifyClass(self, class_option: str) -> dict:
        similarity = process.extractOne(query=class_option, choices=self.classes)
        if similarity:
            if similarity[1] >= 80:
                return {
                    "class_option": similarity[0],
                    "error": False
                }
        return {
            "error": True
        }

    def cleanTags(self, tags: str) -> dict:
        if len(tags) == 0:
            return {
                "error": True
            }
        tags = tags.split(',')

        clean_tags = []
        for tag in tags:
            resp = process.extractOne(query=tag, choices=TAGS)
            if resp[1] >= 95:
                clean_tags.append(resp[0])

        if len(clean_tags) == 0:
            return {
                "error": True
            }

        return {
            "topic_tags": clean_tags,
            "error": False
        }