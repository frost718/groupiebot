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
        if len(media_group) == 0 and update.message.caption and re.search("(P|p)otential (LONG|SHORT|SPOT)", update.message.caption):
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
    update.message.reply_text('Help!')


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def range_calc(update, context):
    print('args:', context.args)
    first = float(context.args[1])
    last = float(context.args[0])
    span = first - last
    s1 = span*23.6/100
    s2 = span*38.2/100
    s3 = span*50/100
    s4 = span*61.8/100
    start_with = 25
    order_size = start_with

    ret = str(first) + " " + str(start_with) + "\n"

    start_with = order_size*2
    order_size = order_size+start_with
    ret += str(round((first-s1), 4)) + " " + str(start_with)+"\n"

    start_with = order_size*2
    order_size = order_size+start_with
    ret += str(round((first-s2), 4)) + " " + str(start_with)+"\n"

    start_with = order_size*2
    order_size = order_size+start_with
    ret += str(round((first-s3), 4)) + " " + str(start_with)+"\n"

    start_with = order_size*2
    order_size = order_size+start_with
    ret += str(round((first-s4), 4)) + " " + str(start_with)+"\n"

    start_with = order_size*2
    order_size = order_size+start_with
    ret += str(last) + " " + str(start_with)+"\n"

    ret += "Total Order Size: "+str(order_size)
    update.message.reply_text(ret)


def main():
    updater = Updater(config["bot_token"], use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # commands
    dp.add_handler(CommandHandler("chatinfo", chatinfo))
    dp.add_handler(CommandHandler("range", range_calc))

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