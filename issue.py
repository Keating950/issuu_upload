import re
from datetime import datetime, date
from os import path


def __parse_date(filepath: str) -> datetime.date:
    filename = str(path.split(filepath)[1])
    date_match = re.search(r"^(\w{3,4})-(\d{2}).*-(19\d{2}|20\d{2})",
                           filename)
    date_str = "-".join(
        (date_match.group(1), date_match.group(2), date_match.group(3))
    ).upper().replace("SEPT", "SEP")
    return datetime.strptime(date_str, "%b-%d-%Y").date()


def __find_web_folder_id(pub_date: datetime.date,
                         web_folders: dict) -> str:
    if pub_date.month > 4:
        return web_folders[
            f"{pub_date.year}-{pub_date.year + 1}"]
    return web_folders[
        f"{pub_date.year - 1}-{pub_date.year}"]


def parse_file(filename: str, web_folders: dict) -> dict:
    vol_no = re.search(r"Vol\.(\d{1,2})", filename).group(1)
    issue_no = re.search(r"Issue\s?(\w+|\d+)", filename).group(1)
    pubdate = __parse_date(filename)
    return {
        "name": f"mcgilltribune.vol{vol_no}.issue{issue_no}",
        "folderIds": __find_web_folder_id(pubdate, web_folders),
        "publishDate": datetime.strftime(pubdate, "%Y-%m-%d"),
        "title": f"The McGill Tribune Vol. {vol_no} Issue {issue_no}",
    }

    # TODO: add encoding function if necessary
    # def encode(self):
