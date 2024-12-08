from src.tasks import club_event_reminder, game_reset_reminder, midnight_reminder, game_midnight_reminder
from src.variables import local_deploy, server_id, channel_ids, webhook_id
from src.views import WelcomeView

import re

from discord.ext import commands
from discord.flags import Intents


# SETTINGS 
test = True if local_deploy else False
#// test_command = True # an overwrite


# for testing
if test:
    channel_ids = {key:channel_ids["testing"] for key in channel_ids}



# Main BOT body
class BOT(commands.Bot):
    
    def __init__(self):
        super().__init__(command_prefix="/", intents=Intents.all(), application_id=1305607183139864669)

    async def on_ready(self):
        print(f"{'Deployed locally' if local_deploy else 'Logged on as'} {self.user}!")

        try:
            synched = await self.tree.sync()
            print(f"Synched {len(synched)} command(s)")
        
        except Exception as error:
            print(error)
        
        server = self.get_guild(server_id)

        club_event_reminder.start(server)
        game_midnight_reminder.start(server)
        midnight_reminder.start(server)
        game_reset_reminder.start(server)

        channel = server.get_channel(channel_ids["welcome"])

        for message in [message async for message in channel.history(limit=None) if message.author.id == webhook_id and message.components][::-1]:
            user_id = re.sub(pattern=r'''\D+''', repl="", string=message.content)
            user = server.get_member(int(user_id))
            
            self.add_view(view=WelcomeView(user=user, stickers=server.stickers), message_id=message.id)
        
        ### TESTS HERE ###
        if local_deploy:
            
            

            pass
        
        ### END ###


bot = BOT()