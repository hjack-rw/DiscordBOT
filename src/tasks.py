from src.variables import local_deploy, channel_ids

from discord.ext import tasks

from datetime import datetime, time, timezone
import pytz

__all__ = ["club_event_reminder", "midnight_reminder"] 


# SETTINGS 
test_events = True if local_deploy else False
#// test_events = True # an overwrite


today = datetime.now(tz=timezone.utc)

time_trigger = {"game":       {"hour": 4,  "minute": 0,  "timezone": [pytz.timezone("Africa/Cairo")]},               # UTC+2
                "midnight":   {"hour": 0,  "minute": 0,  "timezone": [pytz.timezone("Africa/Cairo"), timezone.utc]}, # UTC+2 / UTC
                "club event": {"hour": 19, "minute": 25, "timezone": [timezone.utc]},}                               # UTC

delete_after = time(hour=1, minute=0, second=0)

weekday = {0:"Monday", 1:"Thursday",  2:"Wednesday", 3:"Tuesday", 4:"Friday", 5:"Saturday", 6:"Sunday"}


# for testing
if test_events:
    today = datetime.now()
    after_minutes = 2

    hour, minute  = (int(value) for value in today.strftime("%H/%M").split("/"))
    minute = (minute + after_minutes) if minute <= (59 - after_minutes) else (minute + after_minutes) % 60
    tz = today.astimezone().tzinfo

    time_trigger = {key:{"hour": hour, "minute": minute, "timezone": [tz]} for key in time_trigger}
    channel_ids = {key:channel_ids["testing"] for key in channel_ids}
    
    delete_after = time(hour=0, minute=after_minutes, second=0)
    
    del[hour, minute, tz]

idx = len(time_trigger["midnight"]["timezone"]) - 1


# club event reminder:
@tasks.loop(time=time(hour=time_trigger["club event"]["hour"], 
                      minute=time_trigger["club event"]["minute"], 
                      tzinfo=time_trigger["club event"]["timezone"][0]))
async def club_event_reminder():
    print(f'''"Club event" task running... {today}!''')


# game midnight reminder:
@tasks.loop(time=time(hour=time_trigger["midnight"]["hour"],
                      minute=time_trigger["midnight"]["minute"],
                      tzinfo=time_trigger["midnight"]["timezone"][0]))
async def game_midnight_reminder():
    print(f'''"Game Midnight" task running... {today}!''')


# midnight reminders
@tasks.loop(time=time(hour=time_trigger["midnight"]["hour"],
                      minute=time_trigger["midnight"]["minute"],
                      tzinfo=time_trigger["midnight"]["timezone"][idx]))
async def midnight_reminder(server):
    print(f'''"Midnight" task running... {today}!''')

    # for headmasters (sunday)
    if notify := (today.weekday() == 6):
        message_channel = server.get_channel(channel_ids["headmasters"])
        await message_channel.send("<@&1221884134121668648> Headmasters, remember to take a picture of this week's top 3 students!")

    print(f"It's {weekday[today.weekday()]}! " + ("Notify!" if notify else "Don't notify!"))


# game reset reminder:
@tasks.loop(time=time(hour=time_trigger["game"]["hour"],
                      minute=time_trigger["game"]["minute"],
                      tzinfo=time_trigger["game"]["timezone"][0]))
async def game_reset_reminder():
    print(f'''"Game Reset" task running... {today}!''')


# delete message 
@tasks.loop(time=delete_after) #Create the task
async def delete_message(message):
    await message.delete()