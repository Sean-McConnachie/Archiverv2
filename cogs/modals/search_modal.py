import discord
import numpy as np
from fuzzywuzzy import process

from cogs.modals.validate_modal_inputs import validateModal
from simplicity.json_handler import jLoad
from cogs.embeds.prettyEmbed import prettyEmbed
from table2ascii import table2ascii as t2a, PresetStyle
import datetime as dt


CONFIG = jLoad('static_files/config.json')
TAGS = jLoad('static_files/tags.json')


class searchEmbed:
    def __init__(self, data, results):
        self.page = 0
        self.title = data['topic_name']
        self.relevanceResults = results
        self.upvotesResults = sorted(results, key=lambda d: d['votes_total'], reverse=True)

        self.results = self.relevanceResults
        self.pages = self.make_pages()
        self.show_pages()


    def make_pages(self) -> list:
        if len(self.results) == 0:
            return ["No results."]
        pages = []
        n = 5
        i = 0

        temp = []
        for i in range(len(self.results)):
            if i % n == 0 and i != 0:
                temp = np.array(temp)
                temp = temp.reshape(4, -1)
                temp = temp.tolist()
                temp = t2a(
                    header=["ID", "Topic Name", "Topic tags", "Votes"],
                    body=temp,
                    style=PresetStyle.thin_rounded,
                    first_col_heading=True,
                    last_col_heading=True
                )
                output = f"__**Results for \"{self.title}\"**__\n```{temp}```"
                pages.append(output)
                temp = []
            result = self.results[i]

            temp.append(result['topic_id'])
            temp.append(result['topic_name'])
            temp.append(', '.join(result['topic_tags']))
            temp.append(f"{result['votes_total']}")

        if i % n != n - 1 or i % n != 0:
            temp = np.array(temp)
            temp = temp.reshape(-1, 4)
            temp = temp.tolist()
            temp = t2a(
                header=["ID", "Topic Name", "Topic tags", "Votes"],
                body=temp,
                style=PresetStyle.thin_rounded,
                first_col_heading=True,
                last_col_heading=True
            )
            output = f"__**Results for '{self.title}'**__\n```{temp}```"
            pages.append(output)
            temp = []
        pages = [str(i) for i in pages]
        return pages

    def show_pages(self):
        self.description = self.pages[self.page]

    def previous_page(self):
        if self.page == 0:
            self.page = len(self.pages)
        self.page -= 1
        self.show_pages()

    def next_page(self):
        self.page += 1
        if self.page == len(self.pages):
            self.page = 0

        self.show_pages()

    def relevanceSort(self):
        self.page = 0
        self.results = self.relevanceResults
        self.pages = self.make_pages()
        self.show_pages()

    def upvotesSort(self):
        self.page = 0
        self.results = self.upvotesResults
        self.pages = self.make_pages()
        self.show_pages()


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


class searchModal(discord.ui.Modal, title='Search for a topic'):
    classes = []
    topic_name = discord.ui.TextInput(label="Topic name", custom_id="topic_name")
    class_option = discord.ui.TextInput(label='Class (choose one)', placeholder="Eg. COMPSCI 110", style=discord.TextStyle.short, custom_id="class_option", required=False)
    topic_tags = discord.ui.TextInput(label="Tags (separate with a ,)", custom_id="topic_tags", required=False)

    async def get_results(self, data, interaction) -> list:
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

    async def on_submit(self, interaction: discord.Interaction):
        response = interaction.data
        data = {}
        for i in range(len(response["components"])):
            comp_dict = response["components"][i]["components"][0]
            data[comp_dict["custom_id"]] = comp_dict["value"]

        data = validateModal(data=data, classes=self.classes)

        if "error" in data.keys():
            if "topic_name" in data["error_tags"]:
                embed = prettyEmbed(
                    title="oops",
                    description=data["error"],
                    color=0xFF0000,
                    creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return


        results = await self.get_results(data, interaction)
        embed = searchEmbed(data, results)
        view = searchEmbedView(embed=embed)

        await interaction.user.send(content=embed.description, view=view)

        embed = prettyEmbed(
            message_id="check_dms",
            creator=discord.utils.get(interaction.guild.members, id=355832318532780062)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)