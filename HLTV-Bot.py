import json
import requests
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from time import sleep
from lxml import etree
from khl import Bot, Message
from khl.card import CardMessage, Card, Module, Element, Types, Struct

# get config
with open('./config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# init Bot
bot = Bot(token=config['token'])


# hltv ranking
@bot.command(name='ranking')
async def rankings(msg: Message):
    results = []
    # simulate edge browser
    s = Service('./msedgedriver.exe')
    edge = webdriver.Edge(service=s)
    edge.get("https://www.hltv.org/ranking/teams/")
    session = requests.Session()  # creat session
    cookies = edge.get_cookies()  # get cookies
    for cookie in cookies:  # fill in cookies
        session.cookies.set(cookie['name'], cookie['value'])
    sleep(1)   # wait for the webpage to load
    html = etree.HTML(edge.page_source)  # convert to lxml to analyse
    detail = html.xpath("//div[@class='ranking-header']")
    for i in range(len(detail)):
        if i == 0:
            rank = detail[i].xpath("./span[@class='position']/text()")
            team = detail[i].xpath(
                "./div[@class='relative']/div[@class='teamLine sectionTeamPlayers teamLineExpanded']/span["
                "@class='name']/text()")
            points = detail[i].xpath(
                "./div[@class='relative']/div[@class='teamLine sectionTeamPlayers teamLineExpanded']/span["
                "@class='points']/text()")
            players = detail[i].xpath(
                "./div[@class='relative']/div[@class='playersLine fadedDown']/div["
                "@class='rankingNicknames']/span/text()")
        else:
            rank = detail[i].xpath("./span[@class='position']/text()")
            team = detail[i].xpath(
                "./div[@class='relative']/div[@class='teamLine sectionTeamPlayers ']/span[@class='name']/text()")
            points = detail[i].xpath(
                "./div[@class='relative']/div[@class='teamLine sectionTeamPlayers ']/span[@class='points']/text()")
            players = detail[i].xpath(
                "./div[@class='relative']/div[@class='playersLine ']/div[@class='rankingNicknames']/span/text()")
        # format output
        results.append(f'{rank[0]} {team[0]} {points[0]}')
        results.append('\n   ')
        for player in players:
            results.append(f' · {player}')
        results.append('\n')
    r = ''.join(results)
    # kook send card message
    card_message = CardMessage(Card(Module.Header('Team Rankings'), Module.Section(mode='left', text=r)))
    await msg.reply(card_message)


# bot info
@bot.command(name="hltvinfo")
async def info(msg: Message):
    await msg.reply("Bot written by OOOOMGOSH\nData from www.hltv.org")

# run bot
bot.run()
