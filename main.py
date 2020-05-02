#!/usr/bin/env python3

import hashlib
import logging
import os
import re
from datetime import datetime
from os import path
from sys import argv
from threading import Thread

import requests as r


def file_directory_prompt() -> list:
    folder = input("Enter path to folder: ")
    if not path.isdir(folder):
        raise FileNotFoundError(f"Folder {folder} cannot be located")
    return [f for f in os.listdir(path.abspath(folder))
            if path.splitext(f)[1] == ".pdf"]


def calc_msg_signature(request_params: dict) -> str:
    msg = API_SECRET
    for k, v in sorted(request_params.items(), key=lambda item: item[0]):
        msg += f"{k}{v}"
    msg_hash = hashlib.md5(msg.encode("utf-8"))
    return msg_hash.hexdigest()


def get_web_folders(start_idx: int) -> dict:
    params = {
        "apiKey": API_KEY,
        "action": "issuu.folders.list",
        "startIndex": start_idx,
        "pageSize": 30,
        "format": "json",
    }
    params["signature"] = calc_msg_signature(params)
    # general endpoint for non-upload requests
    resp = r.post("http://api.issuu.com/1_0", params=params)
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


def parse_file(filepath: str) -> dict:
    def parse_date() -> datetime.date:
        name = str(path.split(filepath)[1])
        date_match = re.search(r"^(\w{3,4})-(\d{2}).*-(19\d{2}|20\d{2})",
                               name)
        date_str = "-".join(
            (date_match.group(1), date_match.group(2), date_match.group(3))
        ).upper().replace("SEPT", "SEP")
        return datetime.strptime(date_str, "%b-%d-%Y").date()

    def find_web_folder_id() -> str:
        if pub_date.month > 4:
            return web_folders[
                f"{pub_date.year}-{pub_date.year + 1}"]
        return web_folders[
            f"{pub_date.year - 1}-{pub_date.year}"]

    vol_no = re.search(r"Vol\.(\d{1,2})", filepath).group(1)
    issue_no = re.search(r"Issue\s?(\w+|\d+)", filepath).group(1)
    pub_date = parse_date()
    return {
        "name": f"mcgilltribune.vol{vol_no}.issue{issue_no}",
        "folderIds": find_web_folder_id(),
        "publishDate": datetime.strftime(pub_date, "%Y-%m-%d"),
        "title": f"The McGill Tribune Vol. {vol_no} Issue {issue_no}",
    }


def upload_file(filename: str, session: r.Session) -> None:
    file_data = parse_file(filename)
    file_content = {"file": open(filename, "rb").read()}
    # upload-specific endpoint
    raw_req = r.Request("POST", "http://upload.issuu.com/1_0", data=file_data,
                        files=file_content)
    raw_req.data.update(session.params)
    raw_req.data.update({"signature": calc_msg_signature(raw_req.data)})
    req = session.prepare_request(raw_req)
    resp = session.send(req, timeout=240)
    resp_info = resp.json()["rsp"]["_content"]
    if "error" in resp_info.keys():
        logging.error(f"ERROR: {filename}-{resp.json()}")
    else:
        logging.info(filename)


def upload_file_list(file_list: list) -> None:
    s = r.Session()
    s.params = {
        "apiKey": API_KEY,
        "action": "issuu.document.upload",
        "commentsAllowed": "false",
        "format": "json",
        "language": "en",
        "ratingAllowed": "false",
    }
    error_count = 0
    for f in file_list:
        try:
            upload_file(f, s)
        except (KeyError, re.error):
            logging.exception(path.basename(f))
        except Exception:
            error_count += 1
        finally:
            if error_count >= 10:
                return


def chunk_list(lst, n_chunks):
    return tuple(lst[i::min(n_chunks, len(lst))] for i in range(n_chunks))


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
    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")
    files = tuple(path.join(path.abspath(fp), f) for f in
                  os.listdir(path.abspath(fp))
                  if path.splitext(f)[1] == ".pdf")
    web_folders = get_web_folders(0)
    # Why not use the more obvious multiprocessing.Pool.map function?
    # The thread-safety of Requests's Session object is unclear. This way,
    # each thread gets its own Session.
    chunks = chunk_list(files, 4)
    threads = []
    for i in range(4):
        # enclosing chunk in another tuple to prevent expansion
        threads.append(Thread(target=upload_file_list, args=(chunks[i],)))
        threads[i].start()
    for t in threads:
        t.join()
