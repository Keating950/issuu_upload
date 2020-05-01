import const
from datetime import datetime
import hashlib
import logging
import multiprocessing
import os
import re
import requests as r


def file_directory_prompt() -> list:
    folder = input("Enter path to folder: ")
    if folder == "":
        folder = "/Volumes/Files/Datasets/Tribune Digital Archives"
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Folder {folder} cannot be located")
    return [f for f in os.listdir(os.path.abspath(folder))
            if os.path.splitext(f)[1] == ".pdf"]


def calc_msg_signature(request_params: dict) -> str:
    msg = const.SECRET
    for k, v in sorted(request_params.items(), key=lambda item: item[0]):
        msg += f"{k}{v}"
    msg_hash = hashlib.md5(msg.encode("utf-8"))
    return msg_hash.hexdigest()


def list_web_folders() -> dict:
    params = {
        "apiKey"    : const.KEY,
        "action"    : "issuu.folders.list",
        "startIndex": 0,
        "pageSize"  : 30,
        "format"    : "json",
    }
    params["signature"] = calc_msg_signature(params)
    resp = r.get(const.ENDPOINT, params=params)
    resp.raise_for_status()
    data = resp.json()["rsp"]["_content"]["result"]["_content"]
    return {k: v for k, v in zip(  # keys in range form, e.g. "1998-1999"
        [d["folder"]["name"] for d in data],
        [d["folder"]["folderId"] for d in data])}


def find_web_folder_id(web_folders: dict, filename: str) -> str:
    date_match = re.match(r"(\w{3}[\s\-]\d{2}.*\d{4})", filename)
    pub_date = datetime.strptime(date_match.group(0), "%b-%d-%Y").date()
    if pub_date.month > 4:
        return web_folders[f"{pub_date.year}-{pub_date.year + 1}"]
    return web_folders[f"{pub_date.year - 1}-{pub_date.year}"]


def make_web_folder(s: r.Session, name: str) -> None:
    s.params["folderName"] = name
    s.params["signature"] = calc_msg_signature(dict(s.params))
    resp = s.get(const.ENDPOINT)
    if resp.status_code == 201:
        print(resp)
        raise Exception
    s.params.pop("signature", None)
    print(s.params)
    print(f"Created folder {name}")


def upload_file(s: r.Session, filename: str) -> None:
    # TODO:
    pass


if __name__ == "__main__":
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %("
               "message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="upload.log",
        filemode="a+",
    )
    files = [f for f in os.listdir(
        os.path.abspath("/Volumes/Files/Datasets/Tribune Digital Archives")) if
             os.path.splitext(f)[1] == ".pdf"]
    print(list_web_folders())
    # pool = multiprocessing.Pool()
