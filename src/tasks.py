from src.variables import local_deploy, channel_ids

from discord.ext import tasks

import datetime
import pytz

__all__ = ["club_event_reminder", "midnight_reminder"] 


# SETTINGS 
test_events = True if local_deploy else False
#// test_events = True # an overwrite

time_zone = datetime.timezone.utc
delete_after = datetime.time(hour=1, minute=0, second=0)

time_trigger = {"game": {"hour": 4, "minute": 0}, # UTC+2
                "midnight": {"hour": 0, "minute": 0}, # UTC / UTC+2
                "club event": {"hour": 19, "minute": 25}, # UTC
               }

weekday = {0:"Sunday", 1:"Monday", 2:"Thursday",  3:"Wednesday", 4:"Tuesday", 5:"Friday", 6:"Saturday"}


# for testing
if test_events:
    time_zone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    delete_after = datetime.time(hour=0, minute=3, second=0)
    
    hour, minute  = (int(value) for value in datetime.datetime.today().strftime("%H/%M").split("/"))
    minute = minute + 1 if minute != 59 else 0

    time_trigger = {key:{"hour": hour, "minute": minute} for key in time_trigger}
    channel_ids = {key:channel_ids["testing"] for key in channel_ids}
    
    del[hour, minute]



# club event reminder:
@tasks.loop(time=datetime.time(time_trigger["club event"]["hour"], time_trigger["club event"]["minute"], tzinfo=time_zone))
async def club_event_reminder():
    print(f'''"Club event" task running... {datetime.datetime.now()}''')


# game midnight reminder:
@tasks.loop(time=datetime.time(time_trigger["midnight"]["hour"], time_trigger["midnight"]["minute"], tzinfo=pytz.timezone("Africa/Cairo")))
async def game_midnight_reminder():
    print(f'''"Game Midnight" task running... {datetime.datetime.now()}''')


# midnight reminders
@tasks.loop(time=datetime.time(time_trigger["midnight"]["hour"], time_trigger["midnight"]["minute"], tzinfo=time_zone))
async def midnight_reminder(server):
    print(f'''"Midnight" task running... {datetime.datetime.now()}!''')

    # for headmasters (sunday)
    if datetime.datetime.today().weekday() == 0:
        print(f"It's {weekday[datetime.datetime.today().weekday()]}!")
        message_channel = server.get_channel(channel_ids["headmasters"])
        await message_channel.send("<@&1221884134121668648> Headmasters, remember to take a picture of this week's top 3 students!")


# game reset reminder:
@tasks.loop(time=datetime.time(time_trigger["game"]["hour"], time_trigger["game"]["minute"], tzinfo=pytz.timezone("Africa/Cairo")))
async def game_reset_reminder():
    print(f'''"Game Reset" task running... {datetime.datetime.now()}''')


# delete message 
@tasks.loop(time=delete_after) #Create the task
async def delete_message(message):
    await message.delete()