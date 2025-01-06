from src.db_classes import ExtraVariable, Portkeys
from src.functions import send_webhook, get_image
from src.variables import test_bot, channel_ids, channel_ids_test, system_embed_color

from discord.embeds import Embed
from discord.enums import EntityType, PrivacyLevel
from discord.ext import tasks

from datetime import datetime, time, timedelta, timezone
import re
import time as time_module
import pytz

__all__ = ["game_reset_reminder", "morning_reminder", "club_event_reminder", "game_midnight_reminder", "my_midnight_reminder"] 


time_trigger = {"game_reset":    time(hour=4,  minute=0,  second=0, tzinfo=pytz.timezone("Africa/Cairo")),   # UTC+2
                "morning":       time(hour=7,  minute=0,  second=0, tzinfo=pytz.timezone("Europe/Warsaw")),  # UTC+1
                "club event":    time(hour=19, minute=25, second=0, tzinfo=timezone.utc),                    # UTC
                "game_midnight": time(hour=23, minute=0,  second=0, tzinfo=pytz.timezone("Africa/Cairo")),   # UTC+2
                "my_midnight":   time(hour=0,  minute=0,  second=0, tzinfo=pytz.timezone("Europe/Warsaw")),} # UTC+1

delete_after = {"hours":0, "minutes":0, "seconds":0}

weekday = {0:"Monday", 1:"Tuesday",  2:"Wednesday", 3:"Thursday", 4:"Friday", 5:"Saturday", 6:"Sunday"}

base_date_maintenance = datetime(year=2025, month=1, day=7)


# SETTINGS
# for testing
# test_bot["test_tasks"] = True # overwrite if needed

if test_bot["test_tasks"]:
    now = datetime.now()
    after_minutes = 2

    base_date_maintenance = datetime(year=now.year, month=now.month, day=now.day)

    hour, minute  = (int(value) for value in now.strftime("%H/%M").split("/"))
    if minute <= (59 - after_minutes):
        minute += after_minutes
    else:
        hour += 1
        minute = (minute + after_minutes) % 60

    tz = now.astimezone().tzinfo

    time_trigger = {key:time(hour=hour, minute=minute, tzinfo=tz) for key in time_trigger}
    channel_ids = channel_ids_test
    
    del[hour, minute, tz]



# game reset reminder:
@tasks.loop(time=time_trigger["game_reset"])
async def game_reset_reminder(server):
    today = datetime.now(tz=timezone.utc)
    print(f'''"Game Reset" task running... {today}!''')



# morning reminder:
@tasks.loop(time=time_trigger["morning"])
async def morning_reminder(server):
    today = datetime.now(tz=timezone.utc)
    print(f'''"Morning" task running... {today}!''')

    portkeys = Portkeys().get()

    if test_bot["test_tasks"]:
        birthdays = [385899007991480321 for _ in range(1)]
    else:
        birthdays = [portkey["user_id"] for portkey in portkeys if (portkey["birthday"].month == today.month) and (portkey["birthday"].day == today.day)]

    if birthdays:

        # create birthday notification message
        embed = Embed(color=system_embed_color, description="**GOP  •  " + today.strftime("%d/%m/%Y") + "**\n")
        embed.description += f"Please, wish <@{birthdays[0]}> a **Happy Birthday** <:hugs:1256225688403447888> :heart:"
        embed.set_author(icon_url="https://storage.googleapis.com/chronicle-assets/images/icons/bell-alert-white.png", name="Birthday Announcement!")
        embed.set_thumbnail(url="https://i.pinimg.com/564x/d8/48/59/d848592fca62cc100b148b5b77006248.jpg")

        for birthday in birthdays[1:]:
            embed.add_field(name="", value=f"Wait! There's more...\nPlease, wish <@{birthday}> a **Happy Birthday** as well <:hugs:1256225688403447888> :heart:", inline=False)

        embed.set_footer(text='''"I can see something in the stars...\nToday is a very special day!"''')

        channel = server.get_channel(channel_ids["the-3-broomsticks"])
        await send_webhook(target_channel=channel, user_name="Prof. Trelawney", content="Mention: @everyone", embed=embed)



# club event reminder:
@tasks.loop(time=time_trigger["club event"])
async def club_event_reminder(server):
    trigger_club_event = ExtraVariable(name="trigger_club_event")

    if trigger_club_event.value:
        today = datetime.now(tz=timezone.utc)
        print(f'''"Club event" task running... {today}!''')

        event_info = {"image_id": "event_image",
                      "title": "GOP Club Events!",
                      "subtitle": f"Reminder: {weekday[today.weekday()]}!",
                      "description": "**We start 000!**\nWe will begin with a Quiz, and after roughly 20 min we go over to a Dance!",
                      "location": "HP: Magic Awakened ឵឵(Sphinx)",
                      "footer": '''"Place your right hand on my waist and...\nOne, two, three... One, two, three..."''',
                      "account": "Prof. McGonagall",}
        
        await set_event_and_notification(server, event_info, end_time=(1,0,0), start_time=(19,30,0), today=today)
    
    else:
        trigger_club_event.change_value(to=True)



# game midnight reminder:
@tasks.loop(time=time_trigger["game_midnight"])
async def game_midnight_reminder(server):
    today = datetime.now(tz=timezone.utc)
    print(f'''"Game Midnight" task running... {today}!''')

    delta = datetime(year=today.year, month=today.month, day=today.day) - base_date_maintenance
    if delta.days % 14 == 0:
        print("It's Maintenance! Notify!")

        event_info = {"image_id": "maintenance_image",
                      "title": "",
                      "subtitle": "Reminder: <Maintenance!>",
                      "description": "**It starts 000!**\nDuring this period the game will be unavailable!",
                      "location": "HP: Magic Awakened ឵឵(Sphinx)",
                      "footer": '''"Go on, scram! Or I will hanging you by your thumbs in the dungeons!"''',
                      "account": "Mr. Filch",}
        
        await set_event_and_notification(server, event_info, end_time=(3,0,0), start_time=(22,00,0), today=today)



# midnight reminders
@tasks.loop(time=time_trigger["my_midnight"])
async def my_midnight_reminder(server):
    today = datetime.now(tz=timezone.utc)
    print(f'''"My Midnight" task running... {today}!''')

    # for staff (on sunday)
    if notify := (test_bot["test_tasks"] or today.weekday() == 6):
        channel = server.get_channel(channel_ids["staffroom"])
        
        embed = Embed(color=system_embed_color, description="Dear Staff,\nremember to take a picture of this week's top 3 students!\n")
        embed.set_footer(text='''"But be quick! It is not wise to be wandering around this late hour."''')
        
        await send_webhook(target_channel=channel, user_name="Prof. Dumbledore", content="Mention: <@&1221884134121668648> <@&1221910705318662154>", embed=embed)

    print(f"It's {weekday[today.weekday()]}! " + ("Notify!" if notify else "Don't notify!"))



# delete message 
@tasks.loop(hours=delete_after["hours"], minutes=delete_after["minutes"], seconds=delete_after["seconds"], count=2)
async def delete_message(message):
    if delete_message.current_loop != 0:
        print("Message deleted!")
        await message.delete()


def convert_to_unix_time(date: datetime, mode: str):
    # get a tuple of the date attributes
    date_tuple = (date.year, date.month, date.day, date.hour, date.minute, date.second)

    # convert to unix time
    return f'<t:{int(time_module.mktime(datetime(*date_tuple).timetuple()))}:{mode}>'


async def set_event_and_notification(server, event_info, end_time, start_time, today):
    
    # for testing
    if test_bot["test_tasks"]:
        delete_after["minutes"] = after_minutes * 2
        
        end_after = timedelta(minutes=after_minutes)
        date = now + timedelta(minutes=after_minutes*2)
    else:
        delete_after["hours"] = end_time[0]
        delete_after["minutes"] = start_time[1] - today.minute
        
        if delete_after["minutes"] < 0:
            delete_after["minutes"] = 0
        
        print("h:", delete_after["hours"], " m:", delete_after["minutes"])
        end_after = timedelta(hours=end_time[0], minutes=end_time[1], seconds=end_time[2])
        date = today.replace(hour=start_time[0], minute=start_time[1], second=start_time[2])
    

    # insert weekday and timer
    event_name = event_info["title"] if event_info["title"] else re.search('<(.*)>', event_info["subtitle"]).group(1)
    event_info["subtitle"] = event_info["subtitle"].replace("<", "").replace(">", "")
    event_info["description"] = event_info["description"].replace("000", convert_to_unix_time(date=date, mode="R"))
    
    
    # get image
    channel = server.get_channel(channel_ids["assets"])
    message = [message async for message in channel.history(limit=None) if message.content == event_info["image_id"]][0]


    if not test_bot["test_tasks"]:
    # create event
        try:
            await server.create_scheduled_event(name=event_name,
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
    embed.set_author(icon_url="https://storage.googleapis.com/chronicle-assets/images/icons/bell-alert-white.png", name=event_info["subtitle"])
    embed.add_field(name="Location", value=event_info["location"], inline=False)
    embed.add_field(name="Scheduled for", value=f"{convert_to_unix_time(date=date, mode='t')}", inline=True)
    embed.add_field(name="Duration", value=f"~{delete_after['hours']} {'hours' if delete_after['hours'] > 1 else 'hour'}", inline=True)

    if event_info["footer"]:
        embed.set_footer(text=event_info["footer"])

    channel = server.get_channel(channel_ids["announcements"])
    message = await send_webhook(target_channel=channel, user_name=event_info["account"], content="Mention: <@&1278844289694171260>", embed=embed)
    
    
    if not test_bot["test_tasks"]:
        delete_message.change_interval(hours=delete_after["hours"], minutes=delete_after["minutes"], seconds=delete_after["seconds"])
        delete_message.start(message)