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


def check_input(range_strategy, size_strategy, size_param, size_amount, range1, range2):
    ret = ""
    if not re.search(r'^[\d\.]+$', size_amount):
        ret += "param 4 size_amount needs to be a number!\n"
    if not re.search(r'^[\d\.]+$', range1):
        ret += "param 5 range1 needs to be a number!\n"
    if not re.search(r'^[\d\.]+$', range2):
        ret += "param 6 range2 needs to be a number!\n"
    if not re.search(r'^\w+$', range_strategy):
        ret += "param 1 range_strategy needs to be a 'word' character!\n"
    if not re.search(r'^[a-zA-Z]+$', size_strategy):
        ret += "param 2 size_strategy needs to be a 'word' character!\n"
    if not re.search(r'^[a-zA-Z]+$', size_param):
        ret += "param 3 size_param needs to be a 'word' character!\n"
    return ret


def print_layers(layer_array, size_array):
    if len(layer_array) != len(size_array):
        raise ValueError("Length of layer/size arrays differ! Internal Error.")
    padding = 3
    for lp in layer_array:
        if len(str(lp)) > padding:
            padding = len(str(lp))+1
    total_coins = 0
    ret = "<pre>"
    for i in range(0, len(layer_array)):
        lp = str(layer_array[i])
        ret += "Layer "+str(i+1)+": " + lp
        for _ in range(0, padding-len(lp)):
            ret += " "
        total_coins += round(size_array[i]/layer_array[i], 4)
        ret += "- Size: " + str(size_array[i])+" / "+str(round(size_array[i]/layer_array[i], 4))+"\n"
    for _ in range(0, padding-1):
        ret += " "
    ret += "Total Order Size: "+str(sum(size_array))+" / "+str(round(total_coins, 4))
    ret += "</pre>"
    return ret


def range_fib(first, last):
    span = first - last
    s1 = span*23.6/100
    s2 = span*38.2/100
    s3 = span*50/100
    s4 = span*61.8/100
    ret = [first]
    ret += [round((first-s1), 4)]
    ret += [round((first-s2), 4)]
    ret += [round((first-s3), 4)]
    ret += [round((first-s4), 4)]
    ret += [last]
    return ret


def range_even(first, last, layers):
    span = first - last
    part = round(span/layers, 4)
    ret = [first]
    for i in range(1, layers-1):
        ret += [round(first+(part*i), 4)]
    ret += [last]
    return ret


def size_even_startwith(layers, start_with):
    ret = [start_with]
    for _ in range(1, layers-1):
        ret += [start_with]
    ret += [sum(ret)*2]
    return ret


def size_even_maxtotal(layers, max_total):
    d = sum(size_even_startwith(layers, 1))
    n = round(max_total/d, 2)
    ret = size_even_startwith(layers, n)
    rem = max_total - sum(ret)
    ret[layers-1] = round(ret[layers-1] + rem, 2)
    return ret


def size_double_startwith(layers, start_with):
    ret = [start_with]
    for _ in range(1, layers):
        ret = ret + [round(sum(ret) * 2, 2)]
    return ret


def size_double_maxtotal(layers, max_total):
    d = sum(size_double_startwith(layers, 1))
    n = round(max_total/d, 2)
    ret = size_double_startwith(layers, n)
    rem = max_total - sum(ret)
    ret[layers-1] = round(ret[layers-1] + rem, 2)
    return ret


def layered(update, context):
    if not update.message:
        return
    if len(context.args) != 6:
        return update.message.reply_text("Expecting a total of 6 parameters, please specify them, see /help", quote=False)
    range_strategy = context.args[0]
    size_strategy = context.args[1]
    size_param = context.args[2]
    size_amount = context.args[3]
    first = context.args[5]
    last = context.args[4]
    inputValMsg = check_input(range_strategy, size_strategy, size_param, size_amount, first, last)
    if bool(inputValMsg):
        return update.message.reply_text(inputValMsg, quote=False)
    first = float(first)
    last = float(last)
    size_amount = float(size_amount)

    if range_strategy == "fib":
        layers = 6
        larr = range_fib(first, last)
    elif range_strategy.startswith("even"):
        try:
            layers = int(range_strategy[-1])
            larr = range_even(first, last, layers)
        except:
            return update.message.reply_text("Unable to extract number of layers from: "+range_strategy, quote=False)
    else:
        return update.message.reply_text("range_strategy not supported: "+range_strategy, quote=False)

    if size_strategy == "double":
        if size_param == "startwith":
            sarr = size_double_startwith(layers, size_amount)
        elif size_param == "total":
            sarr = size_double_maxtotal(layers, size_amount)
        else:
            return update.message.reply_text("size_param not supported: "+size_param, quote=False)
    elif size_strategy == "even":
        if size_param == "startwith":
            sarr = size_even_startwith(layers, size_amount)
        elif size_param == "total":
            sarr = size_even_maxtotal(layers, size_amount)
        else:
            return update.message.reply_text("size_param not supported: "+size_param, quote=False)
    else:
        return update.message.reply_text("size_strategy not supported: "+size_strategy, quote=False)

    return update.message.reply_text(print_layers(larr, sarr), quote=False, parse_mode='HTML')


def main():
    updater = Updater(config["bot_token"], use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # commands
    # dp.add_handler(CommandHandler("chatinfo", chatinfo))
    dp.add_handler(CommandHandler("layered", layered, Filters.chat(config["chat_from_id"])))

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
