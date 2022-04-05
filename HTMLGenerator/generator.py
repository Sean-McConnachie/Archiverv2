import os
import discord
from jinja2 import Template


def convert(sender: discord.Member) -> dict:
    return {
        "name": sender.name,
        "id": sender.id,
        "avatar_url": sender.avatar.url
    }


def make_template(data: dict, messages: list, senders: dict):
    with open(os.path.join("HTMLGenerator", 'template.html'), mode='r', encoding="utf-8") as infile:
        template = infile.read()
    # sender will be a dict of dicord.Member
    # senders = {<member_id>: Member}
    # if sender is None then display only their id
    useable_senders = {}
    for sender in senders:
        useable_senders[sender] = convert(senders[sender])

    data["topic_tags"] = ", ".join(data["topic_tags"])
    jinja_template = Template(template)
    rendered = jinja_template.render(data=data, messages=messages, senders=useable_senders)
    return rendered