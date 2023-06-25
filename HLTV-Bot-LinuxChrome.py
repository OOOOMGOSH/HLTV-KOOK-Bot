import json
from time import sleep
import requests
from khl import Bot, Message
from khl.card import CardMessage, Card, Module, Element, Types, Struct
from lxml import etree
from selenium import webdriver
from selenium.webdriver.edge.service import Service

# get config
with open('config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# init Bot
bot = Bot(token=config['token'])


# hltv ranking
@bot.command(name='ranking')
async def rankings(msg: Message):
    results = []
    # simulate edge browser
    s = Service('drivers/chromedriver')
    edge = webdriver.Edge(service=s)
    edge.get("https://www.hltv.org/ranking/teams/")
    session = requests.Session()  # creat session
    cookies = edge.get_cookies()  # get cookies
    for cookie in cookies:  # fill in cookies
        session.cookies.set(cookie['name'], cookie['value'])
    sleep(1)  # wait for the webpage to load
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
        results.append(f'{rank[0]} {team[0]} {points[0]}\n   ')
        for player in players:
            results.append(f' · {player}')
        results.append('\n')
    r = ''.join(results)
    # kook send card message
    card_message = CardMessage(Card(Module.Header('Team Rankings'), Module.Section(mode='left', text=r)))
    await msg.reply(card_message)


# hltv player info
@bot.command(name='player')
async def player(msg: Message, name):
    # simulate edge browser
    s = Service('drivers/chromedriver')
    edge = webdriver.Edge(service=s)
    edge.get(f"https://www.hltv.org/search?query={name}")
    session = requests.Session()  # creat session
    cookies = edge.get_cookies()  # get cookies
    for cookie in cookies:  # fill in cookies
        session.cookies.set(cookie['name'], cookie['value'])
    sleep(1)  # wait for the webpage to load
    html = etree.HTML(edge.page_source)  # convert to lxml to analyse
    detail = html.xpath("//table[@class='table']/tbody")
    # preventing the collection of team info
    if detail[0].xpath("./tr/td[@class='table-header']/text()")[0] == 'Player':
        player_href = detail[0].xpath("./tr/td/a/@href")
        print(player_href)
        for href in range(2 if len(player_href) >= 2 else 1):
            s2 = Service('drivers/chromedriver')
            edge2 = webdriver.Edge(service=s2)
            print(f"https://www.hltv.org{player_href[href]}")
            edge2.get(f"https://www.hltv.org{player_href[href]}")
            session2 = requests.Session()  # creat session
            cookies = edge.get_cookies()  # get cookies
            for cookie in cookies:  # fill in cookies
                session2.cookies.set(cookie['name'], cookie['value'])
            sleep(1)  # wait for the webpage to load
            html2 = etree.HTML(edge2.page_source)  # convert to lxml to analyse
            player_info = html2.xpath("//div[@class='playerInfoWrapper']")
            print(player_info)
            stats = ['\nStatistics (Past 3 months):\n']
            statistics = html2.xpath("//div[@class='playerpage-container']/div[@class='player-stat']")
            print(statistics)
            if statistics:  # statistics returned might be a empty list
                for stat in statistics:
                    type = stat.xpath("./b/text()")
                    value = stat.xpath("./span[@class='statsVal']/p/text()")
                    stats.append(f'{type[0]}: {value[0]}\n')
            s = ''.join(stats)
            player_name = player_info[0].xpath(
                "./div[@class='playerNameWrapper']/div[@class='playerName']/h1[@class='playerNickname']/text()")
            player_real_name = player_info[0].xpath(
                "./div[@class='playerNameWrapper']/div[@class='playerName']/div[@class='playerRealname']/text()")
            player_age = player_info[0].xpath(
                "./div[@class='playerInfo']/div[@class='playerInfoRow playerAge']/span[@class='listRight']/span["
                "@itemprop='text']/text()")
            player_team = player_info[0].xpath(
                "./div[@class='playerInfo']/div[@class='playerInfoRow playerTeam']/span[@class='listRight "
                "text-ellipsis']/span[@itemprop='text']/a/text()")
            player_top = player_info[0].xpath(
                "./div[@class='playerInfo']/div[@class='playerInfoRow playerTop20 top-grid-box']/span[@class='listRight top20ListRight']/a/text()")
            player_top_year = player_info[0].xpath(
                "./div[@class='playerInfo']/div[@class='playerInfoRow playerTop20 top-grid-box']/span[@class='listRight top20ListRight']/span[@class='top-20-year']/text()")
            top = []
            if player_top:  # player_top returned might be an empty list
                for i in range(len(player_top)):
                    top.append(f'{player_top[i]} {player_top_year[i]}')
                    top.append(', ' if i != len(player_top) - 1 else '')
            t = ''.join(top)
            if statistics:  # output player's info only if the player has statistics
                results = [f'{player_name[0]}',
                           f'\nReal name: {player_real_name[0][1:]}' if player_real_name != ['  '] else "\nReal name: N/A",
                           f'\nAge: {player_age[0]}' if player_age else "\nAge: N/A",
                           f'\nTeam: {player_team[0]}' if player_team else "\nTeam: N/A",
                           f'\nTop 20: {t}' if player_top else "\nTop 20: N/A",
                           f'{s}']
            # display data as a card message
            card_message = CardMessage(Card(Module.Header('Player'), Module.Section(''.join(results))))
            await msg.reply(card_message)
    else:
        card_message = CardMessage(Card(Module.Header('Player Not Found')))
        await msg.reply(card_message)


# player info by selecting a specific hltv id
@bot.command(name='player_id')
async def player_id(msg: Message, name, id):
    # simulate edge browser
    s = Service('drivers/chromedriver')
    edge = webdriver.Edge(service=s)
    edge.get(f"https://www.hltv.org/player/{id}/{name}")
    session = requests.Session()  # creat session
    cookies = edge.get_cookies()  # get cookies
    for cookie in cookies:  # fill in cookies
        session.cookies.set(cookie['name'], cookie['value'])
    sleep(1)  # wait for the webpage to load
    html = etree.HTML(edge.page_source)  # convert to lxml to analyse
    player_info = html.xpath("//div[@class='playerInfoWrapper']")
    print(player_info)
    stats = ['\nStatistics (Past 3 months):\n']
    statistics = html.xpath("//div[@class='playerpage-container']/div[@class='player-stat']")
    print(statistics)
    if player_info:  # preventing the collection of data on a blank page
        if statistics:  # statistics returned might be an empty list
            for stat in statistics:
                type = stat.xpath("./b/text()")
                value = stat.xpath("./span[@class='statsVal']/p/text()")
                stats.append(f'{type[0]}: {value[0]}\n')
        else:
            stats.append('No stats from past 3 months')
        s = ''.join(stats)
        player_name = player_info[0].xpath(
            "./div[@class='playerNameWrapper']/div[@class='playerName']/h1[@class='playerNickname']/text()")
        player_real_name = player_info[0].xpath(
            "./div[@class='playerNameWrapper']/div[@class='playerName']/div[@class='playerRealname']/text()")
        player_age = player_info[0].xpath(
            "./div[@class='playerInfo']/div[@class='playerInfoRow playerAge']/span[@class='listRight']/span["
            "@itemprop='text']/text()")
        player_team = player_info[0].xpath(
            "./div[@class='playerInfo']/div[@class='playerInfoRow playerTeam']/span[@class='listRight "
            "text-ellipsis']/span[@itemprop='text']/a/text()")
        player_top = player_info[0].xpath(
            "./div[@class='playerInfo']/div[@class='playerInfoRow playerTop20 top-grid-box']/span[@class='listRight top20ListRight']/a/text()")
        player_top_year = player_info[0].xpath(
            "./div[@class='playerInfo']/div[@class='playerInfoRow playerTop20 top-grid-box']/span[@class='listRight top20ListRight']/span[@class='top-20-year']/text()")
        top = []
        if player_top:
            for i in range(len(player_top)):
                top.append(f'{player_top[i]} {player_top_year[i]}')
                top.append(', ' if i != len(player_top) - 1 else '')
        t = ''.join(top)
        # format output
        results = [f'{player_name[0]}',
                   f'\nReal name: {player_real_name[0][1:]}' if player_real_name != ['  '] else "\nReal name: N/A",
                   f'\nAge: {player_age[0]}' if player_age else "\nAge: N/A",
                   f'\nTeam: {player_team[0]}' if player_team else "\nTeam: N/A",
                   f'\nTop 20: {t}' if player_top else "\nTop 20: N/A",
                   f'{s}']
    else:
        results = ['Player Not Found']
    card_message = CardMessage(Card(Module.Header('Player'), Module.Section(''.join(results))))
    await msg.reply(card_message)


# bot info
@bot.command(name="hltvinfo")
async def info(msg: Message):
    await msg.reply("Bot written by OOOOMGOSH\nData from www.hltv.org")


# run bot
bot.run()
