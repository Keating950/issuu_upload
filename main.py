from CONST import *
import os
import requests as r
import re
import hashlib
import logging
from datetime import datetime


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


def find_web_folder_id(filename: str) -> str:
    date_match = re.match(r"(\w{3}[\s\-]\d{2}.*\d{4})", filename)
    pub_date = datetime.strptime(date_match.group(0), "%b-%d-%Y").date()
    if pub_date.month > 4:
        return f"{pub_date.year}-{pub_date.year + 1}"
    return f"{pub_date.year - 1}-{pub_date.year}"


def make_issu_folder(s: r.Session, name: str) -> None:
    s.params["folderName"] = name
    s.params["signature"] = calc_signature(dict(s.params))
    resp = s.get(ENDPOINT)
    if resp.status_code == 201:
        print(resp)
        raise Exception
    s.params.pop("signature", None)
    print(s.params)
    print(f"Created folder {name}")


if __name__ == "__main__":
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %("
               "message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="upload.log",
        filemode="a+",
    )
    # files = [f for f in os.listdir(
    #     os.path.abspath("/Volumes/Files/Datasets/Tribune Digital Archives"))
    #          if os.path.splitext(f)[1] == ".pdf"]
