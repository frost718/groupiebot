Bot for LifeTime Groupies Chat. telegrambot.py forwards Telegram messages from one Telegram channel to another
based on a regex. Additional commands such as /layered, /pray have been implemented, these are made 
accessible to discord via discordbot.py

# Setup
## Requirements
* Python >= 3.7

## Install python dependencies
```commandline
make init
```

# Configuration
To run this you need to define the following vars in config.yml
```properties
# Bot
bot_token: Telegram Bot token acquired from Botfather
api_id: Telegram API ID
api_hash: Telegram API Hash acquired through telegram dev portal
discord_bot_token: Discord Bot token acquired through discord dev portal
chat_from_id: Telegram chat id to read messages from, acquire with /chatinfo
chat_to_id: Telegram chat id to forward messages to, acquire with /chatinfo
chat_to_id_official: Telegram chat id to forward messages to, acquire with /chatinfo
chat_to_id_alerts: Telegram chat id to post messages to, acquire with /chatinfo
```
```properties
# Media Group reposting
regex: A regular expression that must match the caption of messsage to be reposted
regex_official: A regular expression that must match the caption of messsage to be reposted
from_username: Telegram user ID from whom to forward messages
```
```properties
# /layered command
round_to: 6
fiat_round_to: 2
```
```properties
# Reporting
price_percentage_change_lookback_minutes: 15
price_percentage_change_distance: 15
mover_threshold_minutes: 15
trending_threshold_minutes: 120
```

# Running
## Telegrambot
```commandline
make run_tg_bot
```
## Discordbot
```commandline
make run_discord_bot
```