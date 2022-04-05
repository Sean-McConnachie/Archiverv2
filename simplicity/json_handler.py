import os
import json


def jLoad(path: str):
    with open(path, mode='r') as infile:
        temp = json.load(infile)
        return temp


def jWrite(path: str, file: dict or list):
    with open(path, mode='w') as outfile:
        json.dump(file, outfile, indent=4)


def jWrite_ifnotexists(path: str, file: dict or list):
    if not os.path.exists(path):
        with open(path, mode='w') as outfile:
            json.dump(file, outfile, indent=4)


def jPrint(file: dict or list):
    print(json.dumps(file, indent=4))