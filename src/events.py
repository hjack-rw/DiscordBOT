from src.body import bot
from src.db_classes import WelcomeMessages
from src.functions import draw_infocard
from src.tasks import print_notification
from src.variables import test_bot, server_id, channel_ids_test
from src.views import WelcomeView


# SETTINGS
# for testing
# test_bot["test_events"] = True # overwrite if needed

if test_bot["test_events"]:
    channel_ids = channel_ids_test


# Welcoming event
@bot.event
async def on_member_join(new_user):
    if not new_user.bot:
        server = bot.get_guild(server_id)

        image = draw_infocard(new_user=new_user, all_members=len([member for member in server.members if not member.bot]))
        view = WelcomeView(user=new_user, stickers=server.stickers)

        message = print_notification(server, date=None, event_name="Welcome", variables=[new_user, image, view])

        if not test_bot["test_events"]:
            WelcomeMessages().add(message.id)
    else:
        print(f"BOT: {new_user.name} joined the server!")