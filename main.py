#!/usr/bin/env python3

from issue import parse_file
import const
import hashlib
import logging
import os
from os import path
import requests as r
from sys import argv


def file_directory_prompt() -> list:
    folder = input("Enter path to folder: ")
    if not path.isdir(folder):
        raise FileNotFoundError(f"Folder {folder} cannot be located")
    return [f for f in os.listdir(path.abspath(folder))
            if path.splitext(f)[1] == ".pdf"]


def calc_msg_signature(request_params: dict) -> str:
    msg = const.SECRET
    for k, v in sorted(request_params.items(), key=lambda item: item[0]):
        msg += f"{k}{v}"
    msg_hash = hashlib.md5(msg.encode("utf-8"))
    return msg_hash.hexdigest()


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


def get_web_folders(start_idx: int) -> dict:
    params = {
        "apiKey": const.KEY,
        "action": "issuu.folders.list",
        "startIndex": start_idx,
        "pageSize": 30,
        "format": "json",
    }
    params["signature"] = calc_msg_signature(params)
    resp = r.post(const.ENDPOINT, params=params)
    resp_info = resp.json()["rsp"]["_content"]["result"]
    if "error" in resp_info.keys():
        raise r.exceptions.HTTPError
    data = resp_info["_content"]
    folders = {k: v for k, v in
               zip(  # keys in range form, e.g. "1998-1999"
                   [d["folder"]["name"] for d in data],
                   [d["folder"]["folderId"] for d in data])}
    if resp_info["more"]:
        folders.update(get_web_folders(start_idx + 30))
    return folders


def upload_file(filename: str) -> None:
    file_data = parse_file(filename, web_folders)
    file_content = {"file": open(filename, "rb").read()}
    rawreq = r.Request("POST", const.UPLOAD_ENDPOINT, data=file_data,
                       files=file_content)
    rawreq.data.update(session.params)
    rawreq.data.update({"signature": calc_msg_signature(rawreq.data)})
    req = session.prepare_request(rawreq)
    resp = session.send(req, timeout=240)
    resp_info = resp.json()["rsp"]["_content"]
    if "error" in resp_info.keys():
        print(f"ERROR: {filename}-{resp.json()}")
    else:
        print(f"SUCCESS: {filename}-{resp.json()}")
        logging.info(filename)


if __name__ == "__main__":
    if len(argv) < 2:
        fp = file_directory_prompt()
    elif os.path.exists(argv[1]):
        fp = argv[1]
    else:
        raise ValueError(f"{argv[1]} is not a valid path")
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s"
               "[%(name)s.%(funcName)s:]%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="upload.log",
        filemode="a+",
    )
    files = [path.join(path.abspath(fp), f) for f in
             os.listdir(path.abspath(fp))
             if path.splitext(f)[1] == ".pdf"]
    web_folders = get_web_folders(0)
    session = r.Session()
    session.params = {
        "apiKey": const.KEY,
        "action": "issuu.document.upload",
        "commentsAllowed": "false",
        "format": "json",
        "language": "en",
        "ratingAllowed": "false",
    }
