from dotenv import load_dotenv
from pathlib import Path

import os

path = os.getcwd() + "/src/"
load_dotenv(dotenv_path=Path(path + "env"))

__all__ = ["local_deploy", "server_id", "channel_ids", "webhook_id", "wait_for", "absolute_path", "discord_token", "bot_token", "system_embed_color"] 


local_deploy = False if path == os.getenv("SERVER") else True
server_id = 1221838993071538327
channel_ids = {"welcome": 1221838993071538330,
               "testing": 1287909744409055272,
               "leaderboard_side": 1305917108642910258,
               "headmasters": 1255614086033575977,
               "staffroom": 1283404834804076587,
               "announcements": 1222126723902996480,
               "leaderboard": 1305540120631447654,}
webhook_id = 1310623344122531851

wait_for = 3 # seconds
absolute_path = path
discord_token = os.getenv("DISCORD_TOKEN")
bot_token = os.getenv("DISCORD_BOT_TOKEN")
system_embed_color = 16777215
