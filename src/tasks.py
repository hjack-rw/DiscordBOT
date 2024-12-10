from src.db_classes import ExtraVariable
from src.functions import send_webhook, get_image
from src.variables import local_deploy, channel_ids, channel_ids_test, system_embed_color

from discord.embeds import Embed
from discord.enums import EntityType, PrivacyLevel
from discord.ext import tasks

from datetime import datetime, time, timedelta, timezone
import time as time_module
import pytz

__all__ = ["game_reset_reminder", "club_event_reminder", "game_midnight_reminder", "my_midnight_reminder"] 


# SETTINGS 
test_tasks = True if local_deploy else False
#// test_tasks = True # an overwrite


time_trigger = {"game_reset":    time(hour=4,  minute=0,  second=0, microsecond=0, tzinfo=pytz.timezone("Africa/Cairo")),   # UTC+2
                "club event":    time(hour=19, minute=25, second=0, microsecond=0, tzinfo=timezone.utc),                    # UTC
                "game_midnight": time(hour=0,  minute=0,  second=0, microsecond=0, tzinfo=pytz.timezone("Africa/Cairo")),   # UTC+2
                "my_midnight":   time(hour=0,  minute=0,  second=0, microsecond=0, tzinfo=pytz.timezone("Europe/Warsaw")),} # UTC+1

delete_after = {"hours":1, "minutes":5, "seconds":0}

weekday = {0:"Monday", 1:"Tuesday",  2:"Wednesday", 3:"Thursday", 4:"Friday", 5:"Saturday", 6:"Sunday"}


# for testing
if test_tasks:
    now = datetime.now()
    after_minutes = 2

    hour, minute  = (int(value) for value in now.strftime("%H/%M").split("/"))
    
    if minute <= (59 - after_minutes):
        minute += after_minutes
    else:
        hour += 1
        minute = (minute + after_minutes) % 60

    tz = now.astimezone().tzinfo

    time_trigger = {key:time(hour=hour, minute=minute, tzinfo=tz) for key in time_trigger}
    channel_ids = channel_ids_test
    
    delete_after = {"hours":0, "minutes":after_minutes*2, "seconds":0}
    
    del[hour, minute, tz]



# game reset reminder:
@tasks.loop(time=time_trigger["game_reset"])
async def game_reset_reminder(server):
    today = datetime.now(tz=timezone.utc)
    print(f'''"Game Reset" task running... {today}!''')



# club event reminder:
@tasks.loop(time=time_trigger["club event"])
async def club_event_reminder(server):
    trigger_club_event = ExtraVariable(name="trigger_club_event")

    if trigger_club_event.value:
        today = datetime.now(tz=timezone.utc)
        print(f'''"Club event" task running... {today}!''')

        if test_tasks:
            end_after = timedelta(minutes=after_minutes)
            date = now + timedelta(minutes=after_minutes*2)
        else:
            end_after = timedelta(hours=1)
            date = today.replace(hour=19, minute=30, second=0)
        
        unix_time_timer = convert_to_unix_time(date=date, mode="R")
        unix_time_hour = convert_to_unix_time(date=date, mode="t")

        event_info = {"title": "GOP Club Events!",
                      "description": f"**We start {unix_time_timer}!**\nWe will begin with a Quiz, and after roughly 20 min we go over to a Dance Event!",
                      "location": "HP: Magic Awakened  (Sphinx)"}
        
        # get image
        channel = server.get_channel(channel_ids["assets"])
        message = [message async for message in channel.history(limit=None) if message.content == "event_image"][0]

        # create event
        try:
            await server.create_scheduled_event(name=event_info["title"],
                                                start_time=date.astimezone(),
                                                end_time=(date + end_after).astimezone(),
                                                description=event_info["description"],
                                                location=event_info["location"],
                                                privacy_level=PrivacyLevel.guild_only,
                                                entity_type=EntityType.external,
                                                image=get_image(url=message.attachments[0]))
        except ValueError:
            print("Could not create event!")
        
        
        # create notification message
        embed = Embed(color=system_embed_color, title=event_info["title"], description=event_info["description"])
        embed.set_author(icon_url="https://storage.googleapis.com/chronicle-assets/images/icons/bell-alert-white.png", name=f"Reminder: {weekday[date.weekday()]} Club Events!")
        embed.add_field(name="Location", value=event_info["location"], inline=False)
        embed.add_field(name="Scheduled for", value=f"{unix_time_hour}", inline=True)
        embed.add_field(name="Duration", value="~1 hour", inline=True)


        channel = server.get_channel(channel_ids["announcements"])
        message = await send_webhook(target_channel=channel, user_name="Prof. McGonagall", content="<@&1278844289694171260>", embed=embed)
        delete_message.start(message)
    
    else:
        trigger_club_event.change_value()



# game midnight reminder:
@tasks.loop(time=time_trigger["game_midnight"])
async def game_midnight_reminder(server):
    today = datetime.now(tz=timezone.utc)
    print(f'''"Game Midnight" task running... {today}!''')



# midnight reminders
@tasks.loop(time=time_trigger["my_midnight"])
async def my_midnight_reminder(server):
    today = datetime.now(tz=timezone.utc)
    print(f'''"My Midnight" task running... {today}!''')

    # for staff (on sunday)
    if notify := (test_tasks or today.weekday() == 6):
        channel = server.get_channel(channel_ids["staffroom"])
        
        message = "<@&1221884134121668648> <@&1221910705318662154> Dear Staff, remember to take a picture of this week's top 3 students!"
        await send_webhook(target_channel=channel, user_name="Prof. Dumbledore", content=message)

    print(f"It's {weekday[today.weekday()]}! " + ("Notify!" if notify else "Don't notify!"))



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