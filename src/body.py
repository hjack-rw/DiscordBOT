from src.db_classes import WelcomeMessages
from src.tasks import *
from src.variables import test_bot, server_id, bot_id, channel_ids, channel_ids_test
from src.views import WelcomeView

import re

from discord.errors import NotFound
from discord.ext import commands
from discord.flags import Intents


# SETTINGS
# for testing
# test_bot["test_body"] = True # overwrite if needed
# test_bot["test_events"] = True # overwrite if needed

if test_bot["test_body"]:
    channel_ids = channel_ids_test


# Main BOT body
class BOT(commands.Bot):
    
    def __init__(self):
        super().__init__(command_prefix="/", intents=Intents.all(), application_id=bot_id)

    async def on_ready(self):
        print(f"{'Deployed' if any(test_bot.values()) else 'Logged on as'} {self.user}!")

        try:
            synched = await self.tree.sync()
            print(f"Synched {len(synched)} command(s)")
        
        except Exception as error:
            print(error)
        
        server = self.get_guild(server_id)

        game_reset_reminder.start(server)
        morning_reminder.start(server)
        club_event_reminder.start(server)
        game_midnight_reminder.start(server)
        my_midnight_reminder.start(server)

        for message_id in WelcomeMessages().get_all()[::-1]:
            try:
                channel = server.get_channel(channel_ids["welcome"])
                message = await channel.fetch_message(message_id)
                
                user_id = re.sub(pattern=r'''\D+''', repl="", string=message.content)
                user = server.get_member(int(user_id))
                
                self.add_view(view=WelcomeView(user=user, stickers=server.stickers), message_id=message.id)
            except NotFound:
                pass
        
        if test_bot["test_events"]:
            self.dispatch('member_join', server.get_member(385899007991480321))

        ### TESTS HERE ###
        if test_bot["local_deploy"]:
            
            

            pass
        
        ### END ###


bot = BOT()