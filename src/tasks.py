from src.functions import send_webhook, get_image
from src.variables import local_deploy, channel_ids, system_embed_color

from discord.embeds import Embed
from discord.enums import EntityType, PrivacyLevel
from discord.ext import tasks

from datetime import datetime, time, timedelta, timezone
import time as time_module
import pytz

__all__ = ["club_event_reminder", "game_midnight_reminder", "my_midnight_reminder", "game_reset_reminder"] 


# SETTINGS 
test_events = True if local_deploy else False
#// test_events = True # an overwrite


today = datetime.now(tz=timezone.utc)

time_trigger = {"game":       {"hour": 4,  "minute": 0,  "timezone": [pytz.timezone("Africa/Cairo")]},                                 # UTC+2
                "midnight":   {"hour": 0,  "minute": 0,  "timezone": [pytz.timezone("Africa/Cairo"), pytz.timezone("Europe/Warsaw")]}, # UTC+2 / UTC+1
                "club event": {"hour": 19, "minute": 25, "timezone": [timezone.utc]},}                                                 # UTC

delete_after = {"hours":1, "minutes":5, "seconds":0}

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
    
    delete_after = {"hours":0, "minutes":after_minutes*2, "seconds":0}
    
    del[hour, minute, tz]

idx = len(time_trigger["midnight"]["timezone"]) - 1



# club event reminder:
@tasks.loop(time=time(hour=time_trigger["club event"]["hour"], 
                      minute=time_trigger["club event"]["minute"], 
                      tzinfo=time_trigger["club event"]["timezone"][0]))
async def club_event_reminder(server):
    print(f'''"Club event" task running... {today}!''')

    if test_events:
        end_after = timedelta(minutes=after_minutes*2)
        date = today + timedelta(minutes=after_minutes)
    else:
        end_after = timedelta(hours=1)
        date = today.replace(hour=19, minute=30, second=0)
    
    unix_time_timer = convert_to_unix_time(date=date, mode="R")
    unix_time_hour = convert_to_unix_time(date=date, mode="t")

    event_info = {"title": "GOP Club Events!",
                  "description": f"**We start {unix_time_timer}!**\nWe will begin with a Quiz, and after roughly 20 min we go over to a Dance Event!",
                  "location": "HP: Magic Awakened  (Sphinx)"}
    
    url = "https://media.discordapp.net/attachments/1255614086033575977/1315444388515807292/template.png?ex=67576e8d&is=67561d0d&hm=ffffd3224bb60b5c3681c2017a43dc51238e3e30bafed9f4ad091977895be2d2"


    # create event
    await server.create_scheduled_event(name=event_info["title"],
                                        start_time=date.astimezone(),
                                        end_time=(date + end_after).astimezone(),
                                        description=event_info["description"],
                                        location=event_info["location"],
                                        privacy_level=PrivacyLevel.guild_only,
                                        entity_type=EntityType.external,
                                        image=get_image(url=url))
    
    
    # create notification message
    embed = Embed(color=system_embed_color, title=event_info["title"], description=event_info["description"])
    embed.set_author(icon_url="https://storage.googleapis.com/chronicle-assets/images/icons/bell-alert-white.png", name=f"Reminder: {weekday[date.weekday()]} Club Events!")
    embed.add_field(name="Location", value=event_info["location"], inline=False)
    embed.add_field(name="Scheduled for", value=f"{unix_time_hour}", inline=True)
    embed.add_field(name="Duration", value="~1 hour", inline=True)


    channel = server.get_channel(channel_ids["announcements"])
    message = await send_webhook(target_channel=channel, user_name="Prof. McGonagall", content="<@&1278844289694171260>", embed=embed)
    delete_message.start(message)



# game midnight reminder:
@tasks.loop(time=time(hour=time_trigger["midnight"]["hour"],
                      minute=time_trigger["midnight"]["minute"],
                      tzinfo=time_trigger["midnight"]["timezone"][0]))
async def game_midnight_reminder(server):
    print(f'''"Game Midnight" task running... {today}!''')



# midnight reminders
@tasks.loop(time=time(hour=time_trigger["midnight"]["hour"],
                      minute=time_trigger["midnight"]["minute"],
                      tzinfo=time_trigger["midnight"]["timezone"][idx]))
async def my_midnight_reminder(server):
    print(f'''"My Midnight" task running... {today}!''')

    # for staff (on sunday)
    if notify := (test_events or today.weekday() == 6):
        channel = server.get_channel(channel_ids["staffroom"])
        
        message = "<@&1221884134121668648> <@&1221910705318662154> Dear Staff, remember to take a picture of this week's top 3 students!"
        await send_webhook(target_channel=channel, user_name="Prof. Dumbledore", content=message)

    print(f"It's {weekday[today.weekday()]}! " + ("Notify!" if notify else "Don't notify!"))



# game reset reminder:
@tasks.loop(time=time(hour=time_trigger["game"]["hour"],
                      minute=time_trigger["game"]["minute"],
                      tzinfo=time_trigger["game"]["timezone"][0]))
async def game_reset_reminder(server):
    print(f'''"Game Reset" task running... {today}!''')



# delete message 
@tasks.loop(hours=delete_after["hours"], minutes=delete_after["minutes"], seconds=delete_after["seconds"], count=2)
async def delete_message(message):
    if delete_message.current_loop != 0:
        print("Message deleted!")
        await message.delete()


def convert_to_unix_time(date: datetime, mode: str) -> str:
    # get a tuple of the date attributes
    date_tuple = (date.year, date.month, date.day, date.hour, date.minute, date.second)

    # convert to unix time
    return f'<t:{int(time_module.mktime(datetime(*date_tuple).timetuple()))}:{mode}>'