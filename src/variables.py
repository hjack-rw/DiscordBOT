try:
    from pre_init import *
except ImportError:
    print("failed to import 'test_bot' from pre_init!")
    test_bot = {"local_deploy": False,
                "test_body":    False,
                "test_command": False,
                "test_events":  False,
                "test_tasks":   False,}

from datetime import datetime, time
from dotenv import load_dotenv
from pathlib import Path
from zoneinfo import ZoneInfo

import os

path = os.getcwd() + "/src/"
load_dotenv(dotenv_path=Path(path + "env"))


absolute_path = path
server_id  = 1221838993071538327
bot_id     = 1305607183139864669
webhook_id = 1310623344122531851

channel_ids = {"welcome":           1221838993071538330,
               "assets":            1317172237572509787,
               "testing":           1287909744409055272,
               "headmasters":       1255614086033575977,
               "staffroom":         1283404834804076587,
               "sorting-hat":       1256982350802190426,
               "announcements":     1222126723902996480,
               "portkey-arrival":   1281357645902512168,
               "leaderboard":       1305540120631447654,
               "the-3-broomsticks": 1221920204385161319,}

channel_ids_test = {"assets": 1317172237572509787,}
channel_ids_test.update({key:channel_ids["testing"] for key in channel_ids if key not in ["assets",]})

custom_avatars = {"Prof. Dumbledore": "https://static.wikia.nocookie.net/harrypotter/images/8/82/ProfessorDumbledore.jpg",
                  "Prof. McGonagall": "https://m.natemat.pl/4cccf528bb2fabc88d662c3ac8a519ef,922,0,0,0.png",
                  "Prof. Snape":      "https://images.bravo.de/harry-potter-star-was-stimmt-mit-seinen-augen-nichtjpg,id=ac02185e,b=bravo,w=1200,rm=sk.jpeg",
                  "Prof. Hagrid":     "https://ostatniatawerna.pl/wp-content/cache/thumb/7c/f366d57c85cd27c_730x452.jpg",
                  "Prof. Trelawney":  "https://www.tafce.com/images/thumb/9/9b/Professor_Sybil_Trelawney_HPATOOTP_-_Edited.png/350px-Professor_Sybil_Trelawney_HPATOOTP_-_Edited.png",
                  "Prof. Flitwick":   "https://www.superherodb.com/pictures2/portraits/10/050/13801.jpg?v=1637971200",
                  "Mr. Filch":        "https://www.tafce.com/images/c/c6/Mr_Filch_HPATGOF_-_Edited.png",}

houses = {"gryffindor": {"emoji": "<:gryffindor:1255656359190462484> Gryffindor", "crest": "https://static.wikia.nocookie.net/pottermore/images/1/16/Gryffindor_crest.png/revision/latest?cb=20111112232412"},
          "hufflepuff": {"emoji": "<:hufflepuff:1255656360780238849> Hufflepuff", "crest": "https://static.wikia.nocookie.net/pottermore/images/5/5e/Hufflepuff_crest.png/revision/latest?cb=20111112232427"},
          "ravenclaw" : {"emoji": "<:ravenclaw:1255656362617212999> Ravenclaw",   "crest": "https://static.wikia.nocookie.net/pottermore/images/4/40/Ravenclaw_Crest_1.png/revision/latest?cb=20140604194505"},
          "slytherin" : {"emoji": "<:slytherin:1255656364244729856> Slytherin",   "crest": "https://static.wikia.nocookie.net/pottermore/images/4/45/Slytherin_Crest.png/revision/latest?cb=20111112232353"},
          "BOTS"      : {"emoji": "",                                             "crest": ""},}

housecup_disciplines_names = {0: "Best Partners",
                              1: "Dance Club",
                              2: "Top Wizard",
                              3: "History of Magic",
                              4: "Muggle Studies",
                              5: "Casual Matches",
                              6: "Qudditch",}

gameserver_timezone = ZoneInfo("Africa/Khartoum")
main_timezone = ZoneInfo("Europe/London")

weekdays = {0:"Monday", 1:"Tuesday", 2:"Wednesday", 3:"Thursday", 4:"Friday", 5:"Saturday", 6:"Sunday"}
months   = {"01|January": 1, "02|February": 2, "03|March": 3, "04|April": 4, "05|May": 5, "06|June": 6, "07|July": 7, "08|August": 8, "09|September": 9, "10|October": 10, "11|November": 11, "12|December": 12}

time_trigger = {"game_reset":    time(hour=4,  minute=0,  second=0, tzinfo=gameserver_timezone), # UTC+2 - 03:00 - exact
                "morning":       time(hour=7,  minute=0,  second=0, tzinfo=main_timezone),       # UTC+1 - 08:00 - exact
                "weekly_cards":  time(hour=16, minute=59, second=0, tzinfo=gameserver_timezone), # UTC+2 - 16:00 - exact
                "housecup":      time(hour=19, minute=0,  second=0, tzinfo=gameserver_timezone), # UTC+2 - 18:00 - 24 h early
                "club_events":   time(hour=19, minute=25, second=0, tzinfo=main_timezone),       # UTC+1 - 20:30 - 5 min early
                "game_midnight": time(hour=23, minute=0,  second=0, tzinfo=gameserver_timezone), # UTC+2 - 23:00 - 1 h early
                "midnight":      time(hour=23, minute=0,  second=0, tzinfo=main_timezone),}      # UTC+1 - 24:00 - 1 h early

def notification_dict(is_short=False):
    full_dict = {"Welcome": "event",
                 "Birthday": "morning",
                 "Card - Matagot": "weekly_cards",
                 "Card - Book of Monsters": "weekly_cards",
                 "Card - Cornish Pixies": "weekly_cards",
                 "Housecup": "housecup",
                 "Club Events": "club_events",
                 "Club Points": "club_events",
                 "Maintenance": "game_midnight",
                 "Rankings": "midnight",}
    
    if is_short:
        seen, time_triggers = set(), set(time_trigger.keys())

        short_dict = {}
        for key, value in full_dict.items():
            if (value not in seen) and (value in time_triggers):
                short_dict[key] = value
                seen.add(value)
    
        return short_dict
    return full_dict

wait_for = 2 # seconds
discord_token = os.getenv("DISCORD_TOKEN")
bot_token = os.getenv("DISCORD_BOT_TOKEN")
system_embed_color = 16777215

base_housecup_date = datetime(year=2025, month=1, day=10, tzinfo=gameserver_timezone)