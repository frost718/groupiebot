#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to forward Media Groups (Albums), that is a group of images with a caption
from one Telegram chat to another

Usage:
# python3 groupiebot.py
Press Ctrl-C on the command line or send a signal to the process to stop the bot.
"""

import logging
import re
import telegram
import threading
import yaml
import range_calc
from datetime import datetime

from telegram import InputMediaPhoto
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Config Properties
with open('config.yml', 'rb') as f:
    config = yaml.safe_load(f)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Forward Media Groups to another chat based on timeout
media_group = []
timestamp = datetime.now()
last_media_group_id = -1
bot = telegram.Bot(token=config["bot_token"])


# This is a threaded method, it executes avery 2 seconds
def forward_message_after_timeout():
    threading.Timer(2.0, forward_message_after_timeout).start()
    global media_group
    global timestamp
    global bot
    if len(media_group) > 0 and (datetime.now() - timestamp).total_seconds() > 3:
        bot.send_media_group(chat_id=config["chat_to_id"], media=media_group)
        media_group.clear()


# This gets called on every message the bot receives
def extract_media_and_caption(update, context):
    if update.message and update.message.from_user.username == config["from_username"]:
        global media_group
        global timestamp
        global last_media_group_id
        if len(media_group) == 0 and update.message.caption and re.search(config["caption_regex"], update.message.caption):
            media_group.append(InputMediaPhoto(update.message.photo[-1].file_id, caption=update.message.caption))
            last_media_group_id = update.message.media_group_id
            timestamp = datetime.now()
        elif len(media_group) > 0 and update.message.media_group_id and last_media_group_id == update.message.media_group_id:
            media_group.append(InputMediaPhoto(update.message.photo[-1].file_id))
            timestamp = datetime.now()


# Command Handlers
def chatinfo(update, context):
    update.message.reply_text(update.effective_message.chat_id, quote=False)


def help(update, context):
    """Send a message when the command /help is issued."""
    with open("help.html", "r") as text_file:
        help_text = text_file.read()
    update.message.reply_text(help_text, quote=False, parse_mode='HTML')


def pray(update, context):
    with open("pray.html", "r") as text_file:
        pray_text = text_file.read()
    if len(context.args) != 1:
        return update.message.reply_text("Expecting one ticker as param, eg. SUSHI", quote=False)
    update.message.reply_text(pray_text.replace("SUSHI", context.args[0]), quote=False, parse_mode='HTML')


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def layered(update, context):
    if not update.message:
        return
    if len(context.args) != 6:
        return update.message.reply_text("Expecting a total of 6 parameters, please specify them, see /help", quote=False)
    range_strategy = context.args[0]
    size_strategy = context.args[1]
    size_param = context.args[2]
    size_amount = context.args[3]
    range1 = context.args[4]
    range2 = context.args[5]
    return update.message.reply_text(
        range_calc.layered(range_strategy, size_strategy, size_param, size_amount, range1, range2),
        quote=False, parse_mode='HTML')


def main():
    updater = Updater(config["bot_token"], use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # commands
    # dp.add_handler(CommandHandler("chatinfo", chatinfo))
    dp.add_handler(CommandHandler("layered", layered, Filters.chat(config["chat_from_id"])))
    dp.add_handler(CommandHandler("help", help, Filters.chat(config["chat_from_id"])))
    dp.add_handler(CommandHandler("pray", pray, Filters.chat(config["chat_from_id"])))

    # on noncommand
    dp.add_handler(MessageHandler(Filters.chat(config["chat_from_id"]), extract_media_and_caption))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Start monitoring for captured media groups and forward them
    forward_message_after_timeout()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
