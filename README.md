# groupiebot
Bot for LifeTime Groupies Chat. This bot reposts Telegram messages containing either a single
file attachment (picture) with a caption or multiples (where the first one has a caption - what 
Telegram calls 'media groups') from one Telegram channel to another. A user defined regex must match
the caption in the message, otherwise the message is not forwarded.

To run this you need to define the following vars in config.yml
```
bot_token: Telegram Bot token acquired from Botfather
from_username: Telegram user ID from whom to forward messages
caption_regex: A regular expression that must match the caption of messsage to be reposted
chat_from_id: Telegram chat id to forward message from, acquire with /chatinfo
chat_to_id: Telegram chat id to forward messages to, acquire with /chatinfo
```
