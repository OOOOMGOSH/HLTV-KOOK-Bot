import json
from datetime import datetime
import requests
from khl import Bot, Message
from khl.card import CardMessage, Card, Module, Element, Types, Struct
from lxml import html, etree
from selenium import webdriver
from selenium.webdriver.edge.service import Service

# Get config
with open('config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# init Bot
bot = Bot(token=config['token'])


def simulate_browser(url):
    # Simulate Chrome browser
    s = Service('drivers/msedgedriver')
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 ' \
                 'Safari/537.36 Edg/114.0.1823.58'
    edge_options = webdriver.EdgeOptions()
    edge_options.use_chromium = True
    edge_options.add_argument('--no-sandbox')
    edge_options.add_argument('--window-size=1080,1080')
    edge_options.add_argument('--headless')
    edge_options.add_argument('--disable-gpu')
    edge_options.add_argument(f'user-agent={user_agent}')
    edge = webdriver.Edge(service=s, options=edge_options)
    edge.get(url)
    session = requests.Session()  # Creat session
    cookies = edge.get_cookies()  # Get cookies
    for cookie in cookies:  # Fill in cookies
        session.cookies.set(cookie['name'], cookie['value'])
    return etree.HTML(edge.page_source)  # return page


# team world ranking command
@bot.command(name='ranking')
async def rankings(msg: Message):
    print('/ranking')
    results = []
    page = simulate_browser("https://www.hltv.org/ranking/teams/")  # get page
    # extract content
    title = page.xpath("//div[@class='regional-ranking-header']/text()")[0][:-19]
    ranks = page.xpath("//span[@class='position']/text()")
    teams = page.xpath("//span[@class='name']/text()")
    points = page.xpath("//span[@class='points']/text()")
    players_holder = page.xpath("//table[@class='lineup']")
    for i in range(len(ranks)):
        players = players_holder[i].xpath("./tbody/tr/td[@class='player-holder']/a[@class='pointer']/div["
                                          "@class='nick']/text()")
        # output with Markdown syntax
        results.append(f"**{ranks[i]} {teams[i]} {points[i]}**\n    · {' · '.join(players)}")
    # Send card message
    card_message = CardMessage(
        Card(Module.Header(title), Module.Divider(),
             Module.Section(Element.Text('\n---\n'.join(results)))))
    await msg.reply(card_message)


# player command
@bot.command(name='player')
async def player(msg: Message, name='ZywOo', *id):
    print(f'/player {name} {id}')
    if id:  # directly request player page if id have filled in
        player_href = [f"/player/{id[0]}/{name}"]
    else:  # search by player name
        page = simulate_browser(f"https://www.hltv.org/search?query={name}")
        # check if the player exist
        if page.xpath("//td[@class='table-header']/text()")[0] == 'Player':
            # extract player page url
            player_href = page.xpath("//table[@class='table']")[0].xpath("./tbody/tr/td/a/@href")
        else:
            # request to an empty page
            player_href = ["https://www.hltv.org/player/none"]
    print(player_href)
    for href in range(2 if len(player_href) >= 2 else 1):
        player_page = simulate_browser(f"https://www.hltv.org{player_href[href]}")  # Get content on the page
        stats = ['**Statistics (Past 3 months):**\n']
        statistics = player_page.xpath("//div[@class='playerpage-container']/div[@class='player-stat']")
        if player_page.xpath("//div[@class='playerInfoWrapper']"):  # Check if the player exist
            if statistics:  # Player may not have any statistics
                for data in statistics:
                    type = data.xpath("./b/text()")
                    value = data.xpath("./span[@class='statsVal']/p/text()")
                    stats.append(f'{type[0]}: {value[0]}\n')
            else:
                stats.append('No stats from past 3 months')
            stats_past_three_months = ''.join(stats)
            # Extract content
            region = player_page.xpath("//img[@class='flag']/@alt")
            player_name = player_page.xpath("//h1[@class='playerNickname']/text()")
            player_real_name = player_page.xpath("//div[@class='playerRealname']/text()")
            player_age = player_page.xpath("//span[@class='listRight']/span[@itemprop='text']/text()")
            player_team = player_page.xpath("//span[@class='listRight text-ellipsis']/span[@itemprop='text']/a/text()")
            player_top = player_page.xpath("//span[@class='listRight top20ListRight']/a/text()")
            player_top_year = player_page.xpath("//span[@class='top-20-year']/text()")
            major_winner = player_page.xpath("//div[@class='majorWinner']/b/text()")
            major_mvp = player_page.xpath("//div[@class='majorMVP']/b/text()")
            if player_top:  # player may not have any top 20
                top = [f'{player_top[i]} {player_top_year[i]}' for i in range(len(player_top))]
            else:
                top = ['N/A']
            top_20 = ', '.join(top)
            # Format output with Markdown syntax
            results = [f'**IGN:** {player_name[0]}',
                       f"\n**Real name:** {player_real_name[0][1:] if player_real_name != ['  '] else 'N/A'}",
                       f'\n**Region:** {region[0]}',
                       f"\n**Age:** {player_age[0] if player_age else 'N/A'}",
                       f"\n**Team:** {player_team[0] if player_team else 'N/A'}",
                       f"\n**Top 20:** {top_20}",
                       f"\n**Player achievements:** {major_winner[0] + ' x Major winner' if major_winner else 'N/A'} "
                       f"{major_mvp[0] + ' x Major MVP' if major_mvp else ''}"]
            # Display data as a card message
            card_message = CardMessage(Card(Module.Header(f'Player Profile {player_name[0]}'), Module.Divider(),
                                            Module.Section(Element.Text(''.join(results))),
                                            Module.Divider(), Module.Section(Element.Text(stats_past_three_months))))
            await msg.reply(card_message)
        else:
            card_message = CardMessage(Card(Module.Header('Player Not Found')))
            await msg.reply(card_message)


# top players command
@bot.command(name="top_players")
async def top_teams(msg: Message, player_numbers=10):
    print(f'/top_players {player_numbers}')
    results = []
    # get current date and the date 1 year ago
    dt_now_utc = str(datetime.utcnow()).split(' ')[0]
    dt_previous_year = f"{int(dt_now_utc.split('-')[0]) - 1}-{dt_now_utc.split('-')[1]}-{dt_now_utc.split('-')[2]}"
    # get content on the page
    page = simulate_browser(
        f"https://www.hltv.org/stats/players?startDate={dt_previous_year}&endDate={dt_now_utc}&rankingFilter=Top30")
    # extract content
    players_name = page.xpath("//td[@class='playerCol ']/a/text()")
    players_team = page.xpath("//td[@class='teamCol']/@data-sort")
    players_maps_kd = page.xpath("//td[@class='statsDetail']/text()")
    players_rounds = page.xpath("//td[@class='statsDetail gtSmartphone-only']/text()")
    players_kd_differ = page.xpath("//td[@class='kdDiffCol won']/text()")
    players_rating = page.xpath("//td[@class='ratingCol ratingPositive']/text()")
    # format output with Markdown syntax
    for i in range(int(player_numbers) % 31):
        results.append(f"**#{i + 1}**\n**Player:** {players_name[i]}\n**Team:** {players_team[i]}\n**Statistics ("
                       f"Last 12 months):**\nMaps: {players_maps_kd[i*2]} ** 丨 ** Rounds: {players_rounds[i]} ** 丨 ** "
                       f"K-D Differ: {players_kd_differ[i]}"f" ** 丨 ** K/D: {players_maps_kd[i*2+1]} ** 丨 ** Rating "
                       f"2.0: {players_rating[0]}")
    card_message = CardMessage(
        Card(Module.Header('Top Players'), Module.Divider(),
             Module.Section(Element.Text('\n---\n'.join(results)))))
    await msg.reply(card_message)


# team command
@bot.command(name="team")
async def team(msg: Message, team_name="G2", *id):
    print(f'/team {team_name} {id}')
    if id:  # directly request team page if id have filled in
        team_href = [f"/team/{id[0]}/{team_name}"]
    else:  # search by team name
        page = simulate_browser(f"https://www.hltv.org/search?query={team_name}")
        detail = page.xpath("//table[@class='table']/tbody")
        # check if the team exist
        if page.xpath("//td[@class='table-header']/text()")[0] == 'Team':
            # extract team url
            team_href = page.xpath("//table[@class='table']/tbody")[0].xpath("./tr/td/a/@href")
        else:
            team_href = ["https://www.hltv.org/team/none"]  # Redirect to an empty page
    print(team_href)
    team_page = simulate_browser(f"https://www.hltv.org{team_href[0]}#tab-statsBox")  # Get content on the page
    if team_page.xpath("//div[@class='standard-box profileTopBox clearfix']"):  # Check if the team exist
        # extract content
        name = team_page.xpath("//h1[@class='profile-team-name text-ellipsis']/text()")
        team_region = team_page.xpath("//div[@class='team-country text-ellipsis']/img/@alt")
        world_ranking = team_page.xpath("//div[@class='profile-team-stat']/span[@class='right']/a/text()")
        weeks_in_top30 = team_page.xpath("//div[@class='profile-team-stat']/span[@class='right']/text()")[0]
        average_player_age = team_page.xpath("//div[@class='profile-team-stat']/span[@class='right']/text()")[1]
        coach_real_name = team_page.xpath("//div[@class='profile-team-stat']/a[@class='a-reset right']/text()")
        coach_ign = team_page.xpath(
            "//div[@class='profile-team-stat']/a[@class='a-reset right']/span[@class='bold a-default']/text()")
        last_5_matches_result = team_page.xpath("//a[@class='highlighted-stat text-ellipsis']/div/text()")
        players = team_page.xpath("//a[@class='col-custom']/@title")
        map_win_map = team_page.xpath("//div[@class='map-statistics-row-map-mapname']/text()")
        map_win_percentage = team_page.xpath("//div[@class='map-statistics-row-win-percentage']/text()")
        matches_results = [f"**{name[0]}'s last 5 matches:**\n"]
        map_statistics = ["**Map win statistics past 3 months:**\n"]
        if coach_ign and coach_real_name:  # check if the team has a coach
            coach_name = f"{coach_real_name[0][1:-1]} {coach_ign[0]} {coach_real_name[1][1:]}"
        else:
            coach_name = "N/A"
        if last_5_matches_result:  # check if the team has played amy match
            for i in range(len(last_5_matches_result) // 2):
                matches_results.append(f"{last_5_matches_result[i * 2]}: {last_5_matches_result[i * 2 + 1]}\n")
        else:
            matches_results.append(f"{name[0]} has not played any matches yet")
        if map_win_map:  # check if the team has map win statistics
            for i in range(len(map_win_map)):
                map_statistics.append(f"{map_win_map[i]}: {map_win_percentage[i]}\n")
        else:
            map_statistics.append(f"{name[0]} has played no matches the past 3 months")
        # format output with Markdown syntax
        results = [f"**Team name:** {name[0]}\n",
                   f"**Region:** {team_region[0]}\n",
                   f"**World ranking:** {world_ranking[0]}\n",
                   f"**Weeks in top30 for core:** {weeks_in_top30}\n",
                   f"**Average player age:** {average_player_age if average_player_age else 'N/A'}\n",
                   f"**Coach:** {coach_name}\n",
                   f"**Players:** · {' · '.join(players)}\n"]
        card_message = CardMessage(
            Card(Module.Header(f'Team Profile {name[0]}'), Module.Divider(),
                 Module.Section(Element.Text(''.join(results))), Module.Divider(),
                 Module.Section(Element.Text(''.join(matches_results))), Module.Divider(),
                 Module.Section(Element.Text(''.join(map_statistics)))))
        await msg.reply(card_message)
    else:
        card_message = CardMessage(Card(Module.Header("Team Not Found")))
        await msg.reply(card_message)


# help command
@bot.command(name="help")
async def help(msg: Message):
    print("/help")
    card_message = CardMessage(Card(Module.Header('HLTV-Bot操作指南'), Module.Divider(),
                                    Module.Section(Element.Text('**本机器人适用于查询HLTV队伍/选手信息**')),
                                    Module.Divider(),
                                    Module.Section(Element.Text('**1. `/ranking`**\n    查询队伍排名')),
                                    Module.Divider(), Module.Section(
            Element.Text('**2. `/player {name} {hltv_id(optional)}`**\n    查询选手信息(可能生成多个结果)')),
                                    Module.Divider(),
                                    Module.Section(Element.Text('**3. `/top_players {top xx, default = 10}`**\n    '
                                                                '查询选手排名(近一年)')),
                                    Module.Divider(),
                                    Module.Section(
                                        Element.Text('**4. `/team {name} {id(optional)}`**\n    查询队伍信息')),
                                    Module.Divider(),
                                    Module.Section(Element.Text('> 数据来源: [hltv.org](https://www.hltv.org/)\n'
                                                                '如有其他问题、bug或反馈建议，请私信开发人员:\nOOOOMGOSH#0001'))))
    await msg.reply(card_message)

# run bot
bot.run()
