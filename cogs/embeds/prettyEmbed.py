import discord
import datetime as dt
from simplicity.json_handler import *


class prettyEmbed(discord.Embed):
    def __init__(self,
                 message_id: str or None = None,
                 author: discord.Member or None = None,
                 creator: discord.Member or None = None,
                 **kwargs):
        super().__init__(**kwargs)

        if message_id is not None:
            message = jLoad('embed_messages.json')[message_id]
            self.title = message["title"]
            self.description = message["description"]
            keys = message.keys()
            if "color" in keys:
                self.color = int(message["color"], base=16)
            if "url" in keys:
                self.url = message["url"]
            if "timestamp" in keys:
                self.timestamp = dt.datetime.strptime(message["timestamp"], "%H:%M:%S, %m/%d/%Y")
            if "footer" in keys:
                if "icon_url" in message["footer"].keys():
                    self.set_footer(text=message["footer"]["text"], icon_url=message["footer"]["icon_url"])
                else:
                    self.set_footer(text=message["footer"]["text"])
            else:
                if creator is not None:
                    self.set_footer(text=f"Bot created by {creator.name}",
                                    icon_url=creator.avatar.url)
                else:
                    self.set_footer(text="Bot created by Cyril - 355832318532780062")
            if "image" in keys:
                self.set_image(url=message["image"])
            if "thumbnail" in keys:
                self.set_thumbnail(url=message["thumbnail"])
            if "author" in keys:
                if "url" in message["author"].keys() and "icon_url" in message["author"].keys():
                    self.set_author(name=message["author"]["name"], url=message["author"]["url"], icon_url=message["author"]["icon_url"])
                elif "url" in message["author"].keys():
                    self.set_author(name=message["author"]["name"], url=message["author"]["url"])
                elif "icon_url" in message["author"].keys():
                    self.set_author(name=message["author"]["name"], url=message["author"]["icon_url"])
                else:
                    self.set_author(name=message["author"]["name"])
            else:
                if author is not None:
                    self.set_author(name=author.name,
                                    icon_url=author.avatar.url)

        else:
            if author is not None:
                self.set_author(name=author.name,
                                icon_url=author.avatar.url)
            if creator is not None:
                self.set_footer(text=f"Bot created by {creator.name}",
                                icon_url=creator.avatar.url)
            else:
                self.set_footer(text="Bot created by Cyril - 355832318532780062")

