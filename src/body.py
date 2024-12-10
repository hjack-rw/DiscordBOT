from src.db_classes import WelcomeMessages
from src.tasks import club_event_reminder, game_reset_reminder, my_midnight_reminder, game_midnight_reminder
from src.variables import local_deploy, server_id, channel_ids, channel_ids_test
from src.views import WelcomeView

import re

from discord.errors import NotFound
from discord.ext import commands
from discord.flags import Intents


# SETTINGS 
test = True if local_deploy else False
#// test_command = True # an overwrite


# for testing
if test:
    channel_ids = channel_ids_test



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
        my_midnight_reminder.start(server)
        game_reset_reminder.start(server)

        for message_id in WelcomeMessages().get_all()[::-1]:
            try:
                channel = server.get_channel(channel_ids["welcome"])
                message = await channel.fetch_message(message_id)
                
                user_id = re.sub(pattern=r'''\D+''', repl="", string=message.content)
                user = server.get_member(int(user_id))
                
                self.add_view(view=WelcomeView(user=user, stickers=server.stickers), message_id=message.id)
            except NotFound:
                pass
        
        ### TESTS HERE ###
        if local_deploy:
            
            

            pass
        
        ### END ###


bot = BOT()