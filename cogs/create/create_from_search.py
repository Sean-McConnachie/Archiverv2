import os
import asyncio
import discord
import datetime as dt

from cogs.embeds.prettyEmbed import prettyEmbed
from HTMLGenerator.generator import make_template
from simplicity.json_handler import jLoad, jWrite_ifnotexists


CONFIG = jLoad('config.json')


async def createFromSearch(bot, message: discord.Message):
    if bot.user.id == message.author.id:
        return
    error = False
    try:
        topic_id = int(message.content.split(' ')[0])
        topic_name = " ".join(message.content.split(' ')[1:])
        query = "SELECT * FROM topics WHERE topic_id = $1 AND topic_name = $2 AND dt_closed IS NOT NULL;"
        resp = await bot.db.fetch(query, topic_id, topic_name)
        if isinstance(resp, list) and len(resp) == 1:
            resp = resp[0]
        else:
            error = True
    except:
        error = True

    if error is True:
        embed = prettyEmbed(
            message_id="no_search_result",
            creator=discord.utils.get(message.guild.members, id=355832318532780062)
        )
        temp_msg = await message.reply(embed=embed)
        await asyncio.sleep(10)
        await temp_msg.delete()
        await message.delete()
        return
    else:
        embed = prettyEmbed(
            message_id="make_old_archive",
            creator=discord.utils.get(message.guild.members, id=355832318532780062)
        )
        temp_msg = await message.reply(embed=embed)
        # create the channel

        # create channel and send basic info to channel + insert archive_channel_id into database
        for roles in CONFIG["class_roles"]:
            if roles["display_name"] == resp["class_name"]:
                table_name = roles["table_role_name"]
        for category in CONFIG["application"]["server_data"]["archived_channels_folder_id"]:
            if category["table_role_name"] == table_name:
                archive_category_id = category["category_id"]
        archive_category = discord.utils.get(message.guild.channels, id=archive_category_id)

        # check if this topic already exists
        all_ids = [channel.id for channel in archive_category.channels]
        for channel in archive_category.channels:
            if channel.id == resp["archive_channel_id"]:
                embed = prettyEmbed(
                    title=f"New topic created!",
                    description=f"Go to <#{channel.id}>",
                    color=0x00FF00,
                    creator=discord.utils.get(message.guild.members, id=355832318532780062)
                )
                await temp_msg.edit(embed=embed)
                await asyncio.sleep(10)
                await temp_msg.delete()
                await message.delete()
                return
        # create a new channel if it doesn't already exist
        if len(archive_category.channels) >= 50:
            # too many active topics - remove oldest channel, archive it
            old_channel = archive_category.channels[-1]
            query = "UPDATE topics SET archive_channel_id = $1, archive_dt_created = $2, archive_creator_id = $4 WHERE archive_channel_id = $5;"
            await bot.client.db.execute(query, None, None, None, old_channel.id)
            embed = prettyEmbed(
                title=f"Deleting the oldest channel",
                description=f"The category is full. Deleting {old_channel.name} to create space for your topic.",
                color=0xFF0000,
                creator=discord.utils.get(message.guild.members, id=355832318532780062)
            )
            await temp_msg.edit(embed=embed)
            await old_channel.delete(
                reason=f"The category was full. User {message.author.id} caused the overflow delete.")

        # create the new topic channel
        new_channel = await archive_category.create_text_channel(name=resp["channel_name"])
        query = "UPDATE topics SET archive_channel_id = $1, archive_dt_created = $2, archive_creator_id = $3 WHERE topic_id = $4;"
        await bot.db.execute(query, new_channel.id, dt.datetime.now(), message.author.id, resp["topic_id"])

        basic_content = f"""
                ***{resp["class_name"]}***

                {resp["topic_description"]}

                Tags: *{", ".join(resp["topic_tags"])}*

                **Upvotes:** {{0}} | **Downvotes:** {{1}}
                """
        if resp["upvotes"] is None:
            upvotes = 0
        else:
            upvotes = len(resp["upvotes"])
        if resp["downvotes"] is None:
            downvotes = 0
        else:
            downvotes = len(resp["downvotes"])

        content = basic_content.format(upvotes, downvotes)
        embed = prettyEmbed(
            title=resp["topic_name"],
            description=content,
            color=0x0000FF,
            author=discord.utils.get(message.guild.members, id=resp["creator_id"]),
            creator=discord.utils.get(message.guild.members, id=355832318532780062)
        )
        view = ArchiveChannelView(embed=embed, basic_content=basic_content)
        msg1 = await new_channel.send(embed=embed, view=view)

        # now send all of the messages from the old thread
        query = "SELECT * FROM threads WHERE topic_id = $1"
        temp = await bot.db.fetch(query, resp["topic_id"])
        old_messages = []
        json_messages = []
        senders = []
        colors = CONFIG["application"]["server_data"]["colors"]
        for msg in temp:
            o_dict = {
                "message_id": msg["message_id"],
                "sender_id": msg["sender_id"],
                "dt_sent": msg["dt_sent"],
                "is_tutor": msg["is_tutor"],
                "message_content": msg["message_content"],
                "file_links": msg["file_links"]
            }
            json_messages.append(o_dict)
            o_dict["dt_sent"] = o_dict["dt_sent"].strftime("%H:%M:%S, %m/%d/%Y")
            if resp["creator_id"] == msg["sender_id"]:
                o_dict["color"] = int(colors["creator_embed"], base=16)
            elif msg["is_tutor"] is True:
                o_dict["color"] = int(colors["tutor_embed"], base=16)
            else:
                o_dict["color"] = int(colors["user_embed"], base=16)
            old_messages.append(o_dict)

        # json transcript
        path1 = os.path.join("temp_files", f'JSON_Transcript_{resp["topic_id"]}.json')
        jWrite_ifnotexists(path1, json_messages)
        file1 = discord.File(path1)

        data = {
            "topic_id": resp["topic_id"],
            "topic_name": resp["topic_name"],
            "channel_name": resp["channel_name"],
            "topic_description": resp["topic_description"],
            "class_name": resp["class_name"],
            "creator_id": resp["creator_id"],
            "topic_tags": resp["topic_tags"],
            "dt_created": resp["dt_created"],
            "dt_closed": resp["dt_closed"],
            "upvotes": resp["upvotes"],
            "downvotes": resp["downvotes"],
        }

        # HTML transcript
        senders = {}
        ids = [i["sender_id"] for i in old_messages]
        if resp["creator_id"] not in ids:
            ids.append(resp["creator_id"])
        ids = list(set(ids))
        for i in ids:
            sender = discord.utils.get(message.guild.members, id=i)
            senders[i] = sender

        data["dt_created"] = data["dt_created"].strftime("%H:%M:%S, %m/%d/%Y")
        if data["dt_closed"] is not None:
            data["dt_closed"] = data["dt_closed"].strftime("%H:%M:%S, %m/%d/%Y")

        template = make_template(data, messages=old_messages, senders=senders)
        path2 = os.path.join('temp_files', f'HTML_Transcript_{resp["topic_id"]}.html')
        with open(path2, mode='w', encoding="utf-8") as outfile:
            outfile.write(template)
        file2 = discord.File(path2)

        msg2 = await new_channel.send(files=[file1, file2])
        await msg1.pin()
        await msg2.pin()
        if os.path.exists(path1):
            os.remove(path1)
        if os.path.exists(path2):
            os.remove(path2)

        for msgi in range(len(old_messages)):
            msg = old_messages[msgi]
            sender = senders[msg["sender_id"]]

            embed = messageEmbed(
                message=msg,
                message_c=(msgi, len(old_messages)),
                sender=sender
            )
            await new_channel.send(embed=embed)
        embed = prettyEmbed(
            title=f"New topic created!",
            description=f"Go to <#{new_channel.id}>",
            color=0x00FF00,
            creator=discord.utils.get(message.guild.members, id=355832318532780062)
        )
        await temp_msg.edit(embed=embed)
        await asyncio.sleep(10)
        await temp_msg.delete()

        await message.delete()


class ArchiveChannelView(discord.ui.View):
    def __init__(self, embed: prettyEmbed, basic_content: str):
        super().__init__(timeout=None)
        self.Embed = embed
        self.basic_content = basic_content

    @discord.ui.button(label="Archive this topic", style=discord.ButtonStyle.blurple, emoji=CONFIG["application"]["server_data"]["search_archive_emoji"], custom_id="archive_callback")
    async def archive_callback(self, button: discord.Button, interaction: discord.Interaction):
        query = "SELECT archive_creator_id FROM topics WHERE archive_channel_id = $1;"
        creator_id = await interaction.client.db.fetchval(query, interaction.channel.id)

        if creator_id == interaction.user.id:
            # send modal for confirmation
            modal_view = confirmOldArchiveModal()
            modal_view.topic_name.placeholder = f"{interaction.channel.name}"
            await interaction.response.send_modal(modal_view)
        else:
            # send error to fake user xd
            embed = prettyEmbed(
                message_id="not_creator_archive",
                creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Upvote", emoji=CONFIG["application"]["server_data"]["upvote_emoji"], custom_id="upvote_callback")
    async def upvote_callback(self, button: discord.Button, interaction: discord.Interaction):
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
        query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE archive_channel_id = $3"
        await interaction.client.db.execute(query, upvotes, downvotes, interaction.channel.id)
        await self.update_embed(upvotes=upvotes, downvotes=downvotes, interaction=interaction)
        await interaction.response.defer()

    @discord.ui.button(label="Downvote", emoji=CONFIG["application"]["server_data"]["downvote_emoji"], custom_id="downvote_callback")
    async def downvote_callback(self, button: discord.Button, interaction: discord.Interaction):
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
        query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE archive_channel_id = $3"
        await interaction.client.db.execute(query, upvotes, downvotes, interaction.channel.id)
        await self.update_embed(upvotes=upvotes, downvotes=downvotes, interaction=interaction)
        await interaction.response.defer()

    @discord.ui.button(label="Remove vote", emoji=CONFIG["application"]["server_data"]["removevote_emoji"], custom_id="removevote_callback")
    async def removevote_callback(self, button: discord.Button, interaction: discord.Interaction):
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
        query = "UPDATE topics SET upvotes = $1, downvotes = $2 WHERE archive_channel_id = $3"
        await interaction.client.db.execute(query, upvotes, downvotes, interaction.channel.id)
        await self.update_embed(upvotes=upvotes, downvotes=downvotes, interaction=interaction)
        await interaction.response.defer()

    async def update_embed(self, upvotes: list, downvotes: list, interaction: discord.Interaction):
        temp = self.basic_content
        temp = temp.format(len(upvotes), len(downvotes))
        self.Embed.description = temp
        await interaction.message.edit(embed=self.Embed)


class messageEmbed(discord.Embed):
    def __init__(self, message: dict, message_c: tuple or list, sender: discord.Member):
        super().__init__()
        self.message = message
        # message_id, sender_id, dt_sent, is_tutor, message_content, file_links, color
        self.title = ""
        self.color = self.message["color"]


        self.description = self.message["message_content"]
        if len(self.message["file_links"]) != 0:
            self.description += "\n\n**Files:**"
            for file in message["file_links"]:
                self.description += f"\n    [[{os.path.split(file)[1]}]({file} \"Hovertext\")]"
        self.description += f"\n\n**Tutor** "
        if message["is_tutor"] is True:
            self.description += "✔️"
        else:
            self.description += "❌"


        if sender is None:
            self.set_author(name=message["sender_id"])
        else:
            self.set_author(name=sender.name, icon_url=sender.avatar.url)
        self.timestamp = dt.datetime.strptime(message['dt_sent'], "%H:%M:%S, %m/%d/%Y")
        self.set_footer(text=f"Message {message_c[0]+1}/{message_c[1]}")


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
            embed = prettyEmbed(
                message_id="confirm_archive_on_archive",
                creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
            )
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
