import discord
from simplicity.json_handler import jLoad
from discord.ext import commands
from database.create_db import createDB
from cogs.embeds.prettyEmbed import prettyEmbed
from cogs.modals.create_modal import createModal
from cogs.modals.search_modal import searchModal


CONFIG = jLoad('static_files/config.json')


class ButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)


    async def getUserRoles(self, interaction: discord.Interaction):
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

    @discord.ui.button(label="Create a topic", style=discord.ButtonStyle.blurple, emoji=CONFIG["server_data"]["create_archive_emoji"], custom_id="create_callback")
    async def create_callback(self, interaction: discord.Interaction, button: discord.Button):
        modal_view = createModal()

        useable = await self.getUserRoles(interaction=interaction)

        modal_view.class_option.placeholder = ", ".join(useable)
        modal_view.classes = useable
        await interaction.response.send_modal(modal_view)

    @discord.ui.button(label="Search the archive", style=discord.ButtonStyle.blurple, emoji=CONFIG["server_data"]["search_archive_emoji"], custom_id="search_callback")
    async def search_callback(self, interaction: discord.Interaction, button: discord.Button):
        modal_view = searchModal()

        useable = await self.getUserRoles(interaction=interaction)

        modal_view.class_option.placeholder = ", ".join(useable)
        modal_view.classes = useable
        await interaction.response.send_modal(modal_view)


class CustomClient(commands.Bot):
    def __init__(self, command_prefix, **kwargs):
        super().__init__(command_prefix, **kwargs)
        self.db = kwargs.pop("db")


    async def on_ready(self):
        await createDB(self.db)
        print(f'{self.user} bot is connected and ready')

        # create main messages if they don't already exist
        archive_channel = self.get_guild(CONFIG["server_data"]["guild_id"]).get_channel(CONFIG["server_data"]["archiver_channel_id"])
        messages = archive_channel.history()
        async for m in messages:
            await m.delete()

        view = ButtonView()
        embed = prettyEmbed(message_id="archiver_channel_1", creator=discord.utils.get(archive_channel.guild.members, id=355832318532780062))
        msg = await archive_channel.send(embed=embed, view=view)
        await msg.pin()
