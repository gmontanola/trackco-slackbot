import logging
import json
import re
from datetime import datetime

import httpx
import pytz

from settings import SLACK_TABLE, TIMEZONE

logger = logging.getLogger()
logger.setLevel(logging.INFO)

HTML_RE = re.compile("<.*?>")


def clean_html(text):
    return re.sub(HTML_RE, "", text).replace("\n", "")


def fetch_comments(url, token, start, end, limit=-1):
    headers = {"Authorization": f"bearer {token}"}
    params = {"start": start, "end": end, "limit": limit}

    try:
        logger.info(f"Fetching answers from {start} to {end}...")
        r = httpx.get(url=url, headers=headers, params=params)
    except Exception as e:
        logger.error(f"Something went wrong! Error: {e}")

        raise

    return r.text


def clean_results(response):
    json_r = json.loads(response)
    keys = ["time", "name", "nps_answer", "nps_comment", "last_nps_answer"]

    return [{key: value for key, value in comment.items() if key in keys} for comment in json_r]


def filter_results(results, last_comment_time):
    date_limit = last_comment_time

    return [
        {key: value for key, value in result.items() if result["time"] > date_limit} for result in results
    ]


def order_by_date(results, time_key="time"):
    return sorted(results, key=lambda x: x[time_key])


def convert_dates(results, time_key="time"):
    for result in results:
        result["date"] = datetime.utcfromtimestamp(result[time_key])

    return results


def localize_dates(results, date_key="date", tz="America/Sao_Paulo"):
    timezone = pytz.timezone(tz)
    for result in results:
        result[date_key] = pytz.timezone("UTC").localize(result[date_key]).astimezone(timezone)

    return results


def readable_dates(results, date_key="date"):
    for result in results:
        result[date_key] = result[date_key].strftime("%d/%m/%Y %X")

    return results


def create_message_batch(results):
    for result in results:
        yield (format_message(result))


def format_message(result):
    name = result["name"]
    date = result["date"]
    nps = result["nps_answer"]
    comment = result["nps_comment"]
    last_nps = result["last_nps_answer"]

    try:
        diff_nps = nps - last_nps
    except TypeError:
        diff_nps = None

    if last_nps:
        return (
            f"*{name}*\n"
            f"{date}\n"
            f">{(nps_to_emoji(nps))} *NPS:* {nps}\n"
            f">:memo: *Comentário:* {(clean_html(comment)) if comment else '-'}\n"
            f">{(comparison_to_emoji(diff_nps))} *Último NPS:* {last_nps}"
        )

    else:
        return (
            f"*{name}*\n"
            f"{date}\n"
            f">{(nps_to_emoji(nps))} *NPS:* {nps}\n"
            f">:memo: *Comentário:* {(clean_html(comment)) if comment else '-'}\n"
        )


def comparison_to_emoji(diff):
    if diff > 0:
        return ":arrow_up:"

    elif diff < 0:
        return ":arrow_down:"

    else:
        return ":left_right_arrow:"


def nps_to_emoji(score):
    if score >= 9:
        return ":smile:"

    elif score >= 7 and score < 9:
        return ":neutral_face:"

    else:
        return ":tired_face:"


def update_last_comment_time(results, client, time_key="time"):
    last_comment_time = results[-1][time_key]

    try:
        logger.info(f"Updating DynamoDB table with last comment time of {last_comment_time}")
        client.update_item(
            TableName=SLACK_TABLE,
            Key={"id": {"N": "1"}},
            AttributeUpdates={"date": {"Action": "PUT", "Value": {"N": str(last_comment_time)}}},
        )
    except Exception:
        logger.error(f"Update failed.")

        raise


def get_last_comment_time(client):
    try:
        logger.info(f"Fetching last comment time from DynamoDB")
        response = client.get_item(TableName=SLACK_TABLE, Key={"id": {"N": "1"}},)
        last_comment_time = response["Item"]["date"]["N"]
        logger.info(f"Last comment time value is {last_comment_time}")
    except Exception:
        logger.error(f"Process failed.")

        raise

    return int(last_comment_time)


def prepare_results(response, dynamodb_client):
    last_comment_time = get_last_comment_time(dynamodb_client)

    results = clean_results(response)
    results = order_by_date(results)
    results = convert_dates(results)
    results = localize_dates(results, tz=TIMEZONE)
    results = readable_dates(results)
    results = filter_results(results, last_comment_time)

    return results
