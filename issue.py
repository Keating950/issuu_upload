import re
import logging
from CONST import MONTHS


class Issue:
    def __init__(self, path: str):
        self.name = None
        self.date = None
        self.issue = None
        self.vol = None
        self.path = path
        self.bin = None

        try:
            self.vol = re.search(r"Vol\.(\d{1,2})", path).group(1)
            self.issue = re.search(r"Issue\s?(\w+|\d+)", path).group(1)
        except AttributeError:
            logging.error(f"Encountered error parsing file {path}")
        self.name = f"mcgilltribune.vol{self.vol}.issue{self.issue}"

    # TODO: add encoding function if necessary
    # def encode(self):
