#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Telegram Bot to forward Media Groups (Albums, a group of images with a caption)
from one Telegram chat to another

Usage:
# python3 telegrambot.py
Press Ctrl-C on the command line or send a signal to the process to stop the bot.
"""
import yaml
from lib import range_calc, coingecko
import re
import asyncio
from telethon import TelegramClient
from telethon import events
# from telethon.events import StopPropagation

# Config Properties
with open('config.yml', 'rb') as f:
    config = yaml.safe_load(f)

bot = TelegramClient("telegrambot", config["api_id"], config["api_hash"]).start(bot_token=config["bot_token"])


@bot.on(events.Album(chats=config["chat_from_id"]))
async def forward_album(event):
    if event.sender.username == config["from_username"]:
        if re.search(config["regex"], event.raw_text):
            await event.forward_to(config["chat_to_id"])
        if re.search(config["regex_official"], event.raw_text):
            await event.forward_to(config["chat_to_id_official"])


@bot.on(events.NewMessage(incoming=True, chats=config["chat_from_id"], from_users=config["from_username"]))
async def forward_message(event):
    if not event.message.grouped_id:
        if re.search(config["regex"], event.raw_text):
            await event.forward_to(config["chat_to_id"])
        if re.search(config["regex_official"], event.raw_text):
            await event.forward_to(config["chat_to_id_official"])


@bot.on(events.NewMessage(incoming=True, chats=config["chat_from_id"], pattern='/chatinfo'))
async def chat_info(event):
    await event.respond(str(event.chat_id))


@bot.on(events.NewMessage(incoming=True, chats=config["chat_from_id"], pattern='/pray'))
async def pray(event):
    with open("templates/pray.html", "r") as text_file:
        pray_text = text_file.read()
    ret = "Expecting one ticker as param, eg. SUSHI"
    if len(event.raw_text.split()) == 2:
        ret = pray_text.replace("SUSHI", event.raw_text.split()[1])
    await event.respond(ret, parse_mode='html')


@bot.on(events.NewMessage(incoming=True, chats=config["chat_from_id"], pattern='/layered'))
async def layered(event):
    ret = "Expecting a total of 6 parameters, please specify them, see /help"
    command = event.raw_text.split()
    if len(command) >= 7:
        range_strategy = command[1]
        size_strategy = command[2]
        size_param = command[3]
        size_amount = command[4]
        range1 = command[5]
        range2 = command[6]
        if len(command) == 8:
            ret = range_calc.layered(range_strategy, size_strategy, size_param, size_amount, range1, range2, command[7])
        elif len(command) == 9:
            ret = range_calc.layered(range_strategy, size_strategy, size_param, size_amount, range1, range2, command[7], command[8])
        else:
            ret = range_calc.layered(range_strategy, size_strategy, size_param, size_amount, range1, range2, 0)
    await event.respond(ret, parse_mode='html')


# This is a threaded method, it executes avery 30 seconds
async def sync_coingecko_derivs_and_report_price_movements():
    while True:
        ret = coingecko.sync_perps()
        if ret:
            await bot.send_message(config["chat_to_id_alerts"], ret, parse_mode='html')
        await asyncio.sleep(10)


# This is a threaded method, it executes avery 30 seconds
async def sync_coingecko_trending():
    while True:
        await asyncio.sleep(5)
        ret = coingecko.sync_trending()
        if ret:
            await bot.send_message(config["chat_to_id_alerts"], ret, parse_mode='html')


def main():
    print("starting bot")
    loop = asyncio.get_event_loop()
    # Start monitoring for price movements
    loop.create_task(sync_coingecko_derivs_and_report_price_movements())
    loop.create_task(sync_coingecko_trending())
    loop.run_forever()
    bot.run_until_disconnected()


if __name__ == '__main__':
    main()
