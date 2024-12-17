from pre_init import test_bot

from dotenv import load_dotenv
from pathlib import Path

from datetime import datetime
import os
import sqlite3

path = os.getcwd() + "/src/"
load_dotenv(dotenv_path=Path(path + "env"))

__all__ = ["test_bot", "server_id", "bot_id", "webhook_id", "channel_ids", "channel_ids_test", "custom_avatars", "wait_for", "absolute_path",
           "discord_token", "bot_token", "system_embed_color", "base_date", "db_connection", "db_cursor"] 


server_id = 1221838993071538327
bot_id = 1305607183139864669
webhook_id = 1310623344122531851

channel_ids = {"welcome": 1221838993071538330,
               "assets": 1317172237572509787,
               "testing": 1287909744409055272,
               "leaderboard_side": 1305917108642910258,
               "headmasters": 1255614086033575977,
               "staffroom": 1283404834804076587,
               "announcements": 1222126723902996480,
               "portkey-arrival": 1281357645902512168,
               "leaderboard": 1305540120631447654,}

channel_ids_test = {"assets": 1317172237572509787}
channel_ids_test.update({key:channel_ids["testing"] for key in channel_ids if key != "assets"})

custom_avatars = {"Prof. Dumbledore": "https://static.wikia.nocookie.net/harrypotter/images/8/82/ProfessorDumbledore.jpg",
                  "Prof. McGonagall": "https://m.natemat.pl/4cccf528bb2fabc88d662c3ac8a519ef,922,0,0,0.png",
                  "Prof. Hagrid": "https://ostatniatawerna.pl/wp-content/cache/thumb/7c/f366d57c85cd27c_730x452.jpg",}

wait_for = 3 # seconds
absolute_path = path
discord_token = os.getenv("DISCORD_TOKEN")
bot_token = os.getenv("DISCORD_BOT_TOKEN")
system_embed_color = 16777215
base_date = datetime(year=2000, month=1, day=1)


def connect_db():
    try:
        db = sqlite3.connect(path + '_database.db')
    except sqlite3.Error as error:
        print(error)
    finally:
        return db, db.cursor()
    

db_connection, db_cursor = connect_db()