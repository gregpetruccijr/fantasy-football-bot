import csv
from datetime import datetime
import json
from os import makedirs
from os.path import exists, join
import requests
from time import sleep

from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys


# Start timer
startTime = datetime.now()

# Read Yahoo credentials from json
with open('credentials.json') as f:
    credentials = json.load(f)
USR = credentials['username']
PWD = credentials['password']
LG = credentials['league']
TM = credentials['team']

# Create data file
folder = 'data'
if not exists(folder):
    makedirs(folder)
filename = join(folder, '{:%Y-%m-%d %H%M} week '.format(startTime))


# Requests headers
headers = {
    'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
}


def get_projections(lg, pid):
    # Query projected points
    url = 'https://football.fantasysports.yahoo.com/f1/{}/playernote?pid={}'.format(lg, pid)
    res = requests.get(url, headers=headers)
    for _ in range(10):
        if res.status_code == 200:
            break
        # Retry query
        print('Retrying projections for pid {}'.format(pid))
        sleep(60)
        res = requests.get(url, headers=headers)
    try:
        html = res.json()['content']
    except json.decoder.JSONDecodeError as e:
        print(res, res.status_code, lg, pid)
        raise e
    soup = bs(html, 'lxml')
    rows = soup.select("table.teamtable > tbody > tr")
    points = []
    for row in rows:
        point = row.find_all('td')[4].get_text()
        if point == '':
            continue
        elif point == '-':
            point = '0'
        elif point[0] == '*':
            point = point[1:]
        points.append(point)

    return points


def parse_table(trs2, td_num=1, roster0=False, owner_col_offset=3):
    any_players = False
    for tr in trs2:
        # Parse player info
        tds = tr.find_elements_by_xpath('.//td')
        try:
            div1 = tds[td_num].find_element_by_xpath('.//div/div')
        except NoSuchElementException:
            continue

        # Basic playing info
        div2 = div1.find_element_by_xpath('.//div')
        try:
            a = div2.find_element_by_xpath('.//a')
        except NoSuchElementException:
            continue
        name = a.text
        pid = div1.find_element_by_xpath('.//span/a').get_attribute('data-ys-playerid')
        team, position = div2.find_element_by_xpath('.//span').text.split(' - ')

        # Owner
        if roster0:
            owner = 'self'
        else:
            div3 = tds[td_num + owner_col_offset].find_element_by_xpath('.//div')
            owner = div3.text

        # Get projected points
        points = get_projections(LG, pid)

        # Write output
        with open(filename + '.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([pid, name, team, position, roster0, owner, *points])

        any_players = True

    return any_players


# Start browser
options = Options()
options.headless = True
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(10)  # seconds

# Navigate to Yahoo
URL = 'https://football.fantasysports.yahoo.com/f1/{}/{}'.format(LG, TM)
driver.get(URL)
assert 'Yahoo' in driver.title

# Login
elem = driver.find_element_by_id('login-username')
elem.send_keys(USR)
elem = driver.find_element_by_id('login-signin')
driver.execute_script("arguments[0].click();", elem)
elem.send_keys(Keys.RETURN)
elem = driver.find_element_by_id('login-passwd')
elem.send_keys(PWD)
elem = driver.find_element_by_id('login-signin')
driver.execute_script("arguments[0].click();", elem)

# Parse current week
try:
    elem = driver.find_element_by_css_selector('a.flyout_trigger > span.flyout-title')
    week = elem.text.split(' ')[1]
except NoSuchElementException:
    week = '0'
filename += week

# Parse current players
for i in range(3):
    trs = driver.find_elements_by_css_selector("#statTable{} > tbody > tr".format(i))
    parse_table(trs, 2, True)

# Parse available players
groups = ['O', 'K', 'DEF']
for group in groups:
    for i in range(3):
        URL = 'https://football.fantasysports.yahoo.com/f1/' \
            '{}/players?status=A&pos={}&cut_type=9&stat1=S_PN4W&myteam=0&sort=PTS&sdir=1&count={}'.format(LG, group, i * 25)
        driver.get(URL)
        # Loop over table
        trs = driver.find_elements_by_css_selector("#players-table > div.players > table > tbody > tr")
        if group != 'DEF':
            parse_table(trs)
        else:
            parse_table(trs, owner_col_offset=2)

        # If no players found, skip searching for this position
        if not any_players:
            break

# Close browser
driver.quit()

# Print runtime
print('Total runtime: {}'.format(datetime.now() - startTime))
