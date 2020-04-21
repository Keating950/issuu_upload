from CONST import *
import os
import requests as r
from itertools import chain
import hashlib


def flatmap(f, items):
    return chain.from_iterable(map(f, items))


def calc_signature(request_params: dict) -> str:
    msg = SECRET
    for k, v in sorted(request_params.items(), key=lambda item: item[0]):
        msg += f"{k}{v}"
    msg_hash = hashlib.md5(msg.encode("utf-8"))
    return msg_hash.hexdigest()


def input_directory_prompt() -> list:
    folder = input("Enter path to folder: ")
    if folder == "":
        folder = "/Volumes/Files/Datasets/Tribune Digital Archives"
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Folder {folder} cannot be located")
    return [f for f in os.listdir(os.path.abspath(folder))
            if os.path.splitext(f)[1] == ".pdf"]


def get_issuu_folders():
    params = {
        "apiKey"    : KEY,
        "action"    : "issuu.folders.list",
        "startIndex": 0,
        "pageSize"  : 30,
        "format"    : "json",
    }
    params["signature"] = calc_signature(params)
    resp = r.get(ENDPOINT, params=params)
    resp.raise_for_status()
    data = resp.json()["rsp"]["_content"]["result"]["_content"]
    range_keys = {k: v for k, v in zip(  # keys in range form, e.g. "1998-1999"
        [d["folder"]["name"] for d in data],
        [d["folder"]["folderId"] for d in data])}
    folder_dict = {}
    for k, v in range_keys.items():
        for sub_k in k.split("-"):
            if sub_k.isnumeric():
                folder_dict[int(sub_k)] = v
    print(folder_dict)


if __name__ == "__main__":
    # files = [f for f in os.listdir(
    #     os.path.abspath("/Volumes/Files/Datasets/Tribune Digital Archives"))
    #          if os.path.splitext(f)[1] == ".pdf"]
    # issues = map(lambda f: Issue(f), files)
    print(get_issuu_folders())
