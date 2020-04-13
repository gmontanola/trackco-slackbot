import json
from datetime import datetime, timedelta

import boto3
import httpx
import pytz

from settings import HEADERS, SLACK_WEBHOOK_URL, TIMEZONE, TRACKCO_TOKEN
from utils import create_message_batch, fetch_comments, logger, prepare_results, update_last_comment_time

dynamodb = boto3.client("dynamodb")

now = datetime.utcnow()
today = pytz.timezone("UTC").localize(now).astimezone(pytz.timezone(TIMEZONE))
yesterday = today - timedelta(days=1)


def post_recent_comments(event, context):

    track_response = fetch_comments(
        url="https://api.tracksale.co/v2/report/answer",
        token=TRACKCO_TOKEN,
        start=yesterday.strftime("%Y-%m-%d"),
        end=today.strftime("%Y-%m-%d"),
    )

    results = prepare_results(track_response, dynamodb)

    if any(results):
        logger.info(f"{len(results)} new {'answers' if len(results) > 1 else 'answer'} found!")
        messages = create_message_batch(results)

        try:
            request_counter = 0
            logger.info("Sending message data to Slack")
            for message in messages:
                r = httpx.post(url=SLACK_WEBHOOK_URL, headers=HEADERS, data=json.dumps({"text": message}))
                r.raise_for_status()
                request_counter += 1
            logger.info(
                f"{request_counter} {'messages' if request_counter > 1 else 'message'} were sent to Slack!"
            )

        except httpx.HTTPError:
            logger.error(f"The request failed with status code: {r.status_code}")

            raise

        except Exception:
            logger.error("Something went really wrong")

            raise

        update_last_comment_time(results, dynamodb)

        return "OK"

    else:
        logger.info("No new answers to send.")

        return "Nothing to update."
