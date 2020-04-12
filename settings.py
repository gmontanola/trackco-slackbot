import os

TRACKCO_TOKEN = os.environ.get("TRACKCO_TOKEN")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
TIMEZONE = os.environ.get("SLACK_TIMEZONE")
HEADERS = {"Content-Type": "application-json"}
SLACK_TABLE = os.environ.get("SLACK_TABLE")
