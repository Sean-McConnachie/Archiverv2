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
    errors = {}

    for key, item in data.items():
        if key == "topic_name":
            # verify topic_name
            tname_resp = cleanTopic(data['topic_name'])
            errors["topic_name"] = tname_resp["error"]
        elif key == "class_option":
            # verify class_option
            coption_resp = verifyClass(data['class_option'], classes=classes)
            errors["class_option"] = coption_resp["error"]
        elif key == "topic_tags":
            # verify topic_tags
            ttag_resp = cleanTags(data['topic_tags'])
            errors["topic_tags"] = ttag_resp["error"]
        elif key == "description":
            errors["description"] = None

    overall_error = False

    error_in = "You inputted bad data into these field(s):\n"
    for key in errors.keys():
        value = errors[key]
        if value is True:
            overall_error = True
            if key == "topic_name":
                error_in += " **- Topic name**\n"
            elif key == "class_option":
                error_in += " **- Class option**\n"
            elif key == "topic_tags":
                error_in += " **- Topic tags**\n"
    error_in += "\nPlease look above for more info on valid inputs."

    if overall_error:
        Validated = {"error": error_in}
    else:
        Validated = {}
        for key in errors.keys():
            if key == "topic_name":
                Validated[key] = tname_resp["topic_name"]
                Validated["channel_name"] = tname_resp["channel_name"]
            elif key == "description":
                Validated[key] = data["description"]
            elif key == "class_option":
                Validated[key] = coption_resp["class_option"]
            elif key == "topic_tags":
                Validated[key] = ttag_resp["topic_tags"]

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
