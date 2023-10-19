# -*- coding: utf-8 -*-
# @Time    : 2023/10/16 上午11:46
# @Author  : sudoskys
# @File    : discord.py
# @Software: PyCharm
# This example requires the 'message_content' intent.

import nextcord
from nextcord.ext import commands

TESTING_GUILD_ID = 123456789  # Replace with your guild ID

bot = commands.Bot()


@bot.command()
async def hello(ctx):
    await ctx.reply("Hello!")


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.slash_command(description="My first slash command", guild_ids=[TESTING_GUILD_ID])
async def hello(interaction: nextcord.Interaction):
    await interaction.send("Hello!")


bot.run('your token here')
