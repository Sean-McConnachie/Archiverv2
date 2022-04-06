import string
from fuzzywuzzy import process
from simplicity.json_handler import jLoad


TAGS = jLoad('static_files/tags.json')


def validateModal(data: dict, classes: list) -> dict:
    """

    :param data: data can come with different keys from create_modal.py or search_modal.py

    create_modal.py:
        data.keys() = ["topic_name", "description", "class_option", "topic_tags"]
    search_modal.py:
        data.keys() = ["class_option", "topic_tags"]

    :return: Validated: Returns a dict with {"error": "..."} if error is found, or
    return: Validated: Returns a dict with {"data": ...} if no errors and data is safe
    """
    # topic_name, description, class_option, topic_tags possible keys
    Validated = {}
    error_tags = []
    overall_error = False
    error_in = "You inputted bad data into these field(s):\n"

    for key, item in data.items():
        if key == "topic_name":
            temp = cleanTopic(name=data["topic_name"])
            if temp["error"] is True:
                error_tags.append("topic_name")
                overall_error = True
                error_in += " **- Topic name**\n"
            else:
                Validated["topic_name"] = temp["topic_name"]
                Validated["channel_name"] = temp["channel_name"]
        elif key == "class_option":
            temp = verifyClass(class_option=data["class_option"], classes=classes)
            if temp["error"] is True:
                error_tags.append("class_option")
                overall_error = True
                error_in += " **- Class option**\n"
                if "class_option" in temp.keys():
                    Validated["class_option"] = temp["class_option"]
            else:
                Validated["class_option"] = temp["class_option"]
        elif key == "topic_tags":
            temp = cleanTags(tags=data["topic_tags"])
            if temp["error"] is True:
                error_tags.append("topic_tags")
                overall_error = True
                error_in += " **- Topic tags**\n"
                if "topic_tags" in temp.keys():
                    Validated["topic_tags"] = temp["topic_tags"]
            else:
                Validated["topic_tags"] = temp["topic_tags"]
        elif key == "description":
            Validated["description"] = data["description"]
    error_in += "\nPlease look above for more info on valid inputs."

    if overall_error:
        Validated["error"] = error_in
        Validated["error_tags"] = error_tags

    return Validated


def cleanTopic(name: str) -> dict:
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
        if (char == "-" and previous == "-") or \
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


def verifyClass(class_option: str, classes: list) -> dict:
    if class_option == "" or class_option is None:
        return {
            "error": True,
            "class_option": None
        }

    similarity = process.extractOne(query=class_option, choices=classes)
    if similarity:
        if similarity[1] >= 80:
            return {
                "class_option": similarity[0],
                "error": False
            }
    return {
        "error": True
    }


def cleanTags(tags: str) -> dict:
    if tags is None or len(tags) == 0:
        return {
            "topic_tags": None,
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
