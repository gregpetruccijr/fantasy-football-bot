import ffbot

# Yahoo league/team id
# Visit your team at https://football.fantasysports.yahoo.com/f1/, and the url will also include your league and team ID
league = 123456
team = 1
positions = 'QB, WR, WR, WR, RB, RB, TE, W/R/T, K, DEF, BN, BN, BN, BN, IR'
week = ffbot.current_week()

# Scrape data for current and available players, and their point forecasts for each week
df = ffbot.scrape(league)

# Optional save data to CSV, and load latest data
#ffbot.save(df, week)
#df, week = ffbot.load()

# Optimize the assignment of players to positions each week to maximize remaining season discounted total points (points this week are worth more than points in future weeks)
#  decides which players to add and drop
#  optimization is repeated for current roster, for one player add/drop, two player add/drops, etc.
ffbot.optimize(df, week, team, positions)

# Output will look like:
'''Add                        Drop                Total points    Discounted points
-------------------------  ----------------  --------------  -------------------
                                                   +1583.94              +367.51
Kansas City                A.J. Green                -16.27                +2.24
Matt Bryant                Joey Slye                  +4.60                +1.67
Dede Westbrook             Kenyan Drake               +4.27                +0.65
Jordan Howard - W (Oct 2)  Marvin Jones Jr.          +10.37               +17.23'''
#  which means that optimal weekly rosters of your current players scores 1583.94 points
#  across the season and 367.51 discounted points (points in week 1 are worth more than week 12).
#  The best free agent to add is Kansas City by dropping A.J. Green, which increases discounted points by 2.24 (although lowers total season points by 16.27).
#  Two other free agent pickups improve discounted points.
#  Only one Waiver claim (for Jordon Howard) increases discounted points.
