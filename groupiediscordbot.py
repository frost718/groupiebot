#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to calculate layered limit orders for two extreme points on a chart

Usage:
# python3 groupiediscordbot.py
Press Ctrl-C on the command line or send a signal to the process to stop the bot.
"""

import re
import yaml
import range_calc

import discord
from discord.ext import commands

# Config Properties
with open('config.yml', 'rb') as f:
    config = yaml.safe_load(f)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)


@bot.command()
async def layered(ctx, *, message: str):
    ret = "Expecting a total of 6 parameters, please specify them, see /help"
    args = message.split()
    if len(args) >= 6:
        range_strategy = args[0]
        size_strategy = args[1]
        size_param = args[2]
        size_amount = args[3]
        range1 = args[4]
        range2 = args[5]
        if len(args) == 7:
            ret = range_calc.layered(range_strategy, size_strategy, size_param, size_amount, range1, range2, args[6])
        elif len(args) == 8:
            ret = range_calc.layered(range_strategy, size_strategy, size_param, size_amount, range1, range2, args[6], args[7])
        else:
            ret = range_calc.layered(range_strategy, size_strategy, size_param, size_amount, range1, range2, 0)
    await ctx.send(re.sub(r'<.*?>', '', ret))


@bot.command()
async def layered_help(ctx):
    """Send a message when the command /help is issued."""
    with open("help.html", "r") as text_file:
        help_text = text_file.read()
    await ctx.send(re.sub(r'<.*?>', '', help_text))


bot.run(config['discord_bot_token'])
