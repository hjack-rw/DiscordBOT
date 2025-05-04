from src.db_classes import WelcomeMessages
from src.tasks import *
from src.variables import test_bot, server_id, bot_id, channel_ids, channel_ids_test
from src.views import WelcomeView, MemberView

import re

from datetime import datetime, timedelta
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

        #game_reset_reminder.start(server)
        morning_reminder.start(server)
        weekly_cards_reminder.start(server)
        housecup_reminder.start(server)
        club_events_reminder.start(server)
        game_midnight_reminder.start(server)
        midnight_reminder.start(server)


        # reactivate WelcomeViews
        for welcome_message in WelcomeMessages(date__greatequal=(datetime.now() - timedelta(days=14)), order=["date-"]).get():
            try:
                channel = server.get_channel(channel_ids["welcome"])
                
                message = await channel.fetch_message(welcome_message["message_id"])
                user = server.get_member(welcome_message["user_id"])
                
                self.add_view(view=WelcomeView(user=user, stickers=server.stickers), message_id=message.id)
            except NotFound:
                pass

        
        # reactivate MemberView
        channel = server.get_channel(channel_ids["sorting-hat"])
        bot_message_id = 1369590818192494668

        message = await channel.fetch_message(bot_message_id)
        message_view = MemberView(server.members, message)

        self.add_view(view=message_view, message_id=bot_message_id)
        await message_view.print_list()
        

        if test_bot["test_events"]:
            self.dispatch('member_join', server.get_member(385899007991480321))
            self.dispatch('member_remove', server.get_member(385899007991480321))

        ### TESTS HERE ###
        if test_bot["local_deploy"]:
            
            
            
            pass
        
        ### END ###


bot = BOT()