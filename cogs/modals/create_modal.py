import string
import discord
import datetime as dt
from fuzzywuzzy import process
from simplicity.json_handler import jLoad
from cogs.embeds.prettyEmbed import prettyEmbed


from cogs.create.create_from_new import createFromNew


CONFIG = jLoad('config.json')
TAGS = jLoad('tags.json')


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

        description = data["description"]

        data = {
            "topic_name": tname_resp["topic_name"],
            "channel_name": tname_resp["channel_name"],
            "description": description,
            "class_option": coption_resp["class_option"],
            "topic_tags": ttag_resp["topic_tags"]
        }


        await createFromNew(interaction=interaction, data=data)


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