# NPS Bot Track.co + Slack

This simple Slack bot gathers new NPS answers from [Track.co](https://tracksale.co/) using it's [API](https://api.tracksale.co/) and parsing the results to a friendly format and posting to a channel.

It runs on AWS Lambda and stores a little piece of data on DynamoDB. This project can fit the Free Tier without any problem. This started as a weekend project but I'll probably update it to improve my coding skills.

![Screen capture](https://i.imgur.com/C0J7nEy.png)

## How to use it

1. Clone this repo
2. Create a simple DynamoDB table
3. Create two parameters with type set as **SecureString** at [AWS Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html):
    * *TRACKCO_TOKEN:* your Track.co API token
    * *SLACK_WEBHOOK_URL:* the webhook Slacks provides you for incoming messages.
4. Install and configure [Serverless Framework](https://serverless.com/framework/docs/getting-started/)
5. Run `sls plugin install -n serverless-python-requirements`
6. Edit `serverless.yml` and change some variables:
    * *slackTable:* the name of your DynamoDB table you've just created.
    * *slackTimezone:* the timezone of your Slack channel.
7. Inside the project directory run `sls deploy` to deploy it to AWS. If you want to change the **update rate** for the bot (the _default_ is 30 minutes) use `sls deploy --rate RATE` where RATE is a time expression like `15 minutes` or `2 hours`.

## Limitations

* Since there is **no webhook** available for public use and the `start`/`end` parameters for the requests **accept only** `yyyy-mm-dd` as date filtering options, there is no reliable way of getting only new answers. The only way I found to mimic a webhook is to constantly request data from Track.co API and **store the latest answer time on a DynamoDB table**. This value will filter further requests.

* There is a `last_nps_answer` field on the response but apparently it is not working properly. I used it to create a comparison with emojis between the last value and the actual but without real data there is no use for it.

## TODO

1. **Better instructions** - Self describing
2. **Tests** - I guess this project is a good opportunity to start testing my code.
3. **CI/CD** - Truth to be told: my experience with CI/CD matches my experience with tests.
4. **Remove hardcoded stuff** - There is plenty of hardcoded variables and I'll try to refactor and make the code cleaner and able to handle different users needs.
5. **Slash commands** - A `/nps` or `/nps start end` command to make this bot more interactive.
6. **Localization** - If you don't speak portuguese, you will learn a little bit with this bot messages.
7. **Lambda Layers** - Instead of packaging the dependencies with the project with _serverless-python-requirements_.
