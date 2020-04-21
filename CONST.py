from os import getenv

MONTHS = {
    "Jan" : "01",
    "Feb" : "02",
    "Mar" : "03",
    "Apr" : "04",
    "May" : "05",
    "Jun" : "06",
    "Jul" : "07",
    "Aug" : "08",
    "Sept": "09",
    "Oct" : "10",
    "Nov" : "11",
    "Dec" : "12",
}
UPLOAD_ENDPOINT = "http://upload.issuu.com/1_0"
ENDPOINT = "http://api.issuu.com/1_0"
KEY = getenv("KEY")
SECRET = getenv("SECRET")
