from src.db_classes import ExtraVariable, Portkeys
from src.functions import send_webhook, get_image
from src.variables import test_bot, channel_ids, channel_ids_test, system_embed_color

from datetime import datetime, time, timedelta, timezone
import re
import time as time_module
import pytz

from discord.embeds import Embed
from discord.enums import EntityType, PrivacyLevel
from discord.ext import tasks


__all__ = ["morning_reminder", "club_event_reminder", "game_midnight_reminder", "midnight_reminder"] 


time_trigger = {"game_reset":    time(hour=4,  minute=0,  second=0, tzinfo=pytz.timezone("Africa/Cairo")),   # UTC+2 - exact
                "morning":       time(hour=7,  minute=0,  second=0, tzinfo=pytz.timezone("Europe/Warsaw")),  # UTC+1 - exact
                "club event":    time(hour=19, minute=25, second=0, tzinfo=timezone.utc),                    # UTC   - 5 min early
                "game_midnight": time(hour=23, minute=0,  second=0, tzinfo=pytz.timezone("Africa/Cairo")),   # UTC+2 - 1 h early
                "midnight":      time(hour=23, minute=0,  second=0, tzinfo=timezone.utc),}                   # UTC   - 1 h early

delete_after = {"hours":0, "minutes":0, "seconds":0}

weekdays = {0:"Monday", 1:"Tuesday", 2:"Wednesday", 3:"Thursday", 4:"Friday", 5:"Saturday", 6:"Sunday"}


# SETTINGS
# for testing
# test_bot["test_tasks"] = True # overwrite if needed

if test_bot["test_tasks"]:
    now = datetime.now()
    after_minutes = 2
    delete_after["minutes"] = after_minutes * 2

    # replace time
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
#@tasks.loop(time=time_trigger["game_reset"])
#async def game_reset_reminder(server):
#    today = datetime.now(tz=timezone.utc)
#    print(f'''"Game Reset" task running... {today}!''')



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
        #print(f'''"Club event" task running... {today}!''')

        event_info = {"image_id":    "event_image",
                      "title":       "GOP Club Events!",
                      "subtitle":   f"Reminder: {weekdays[today.weekday()]}!",
                      "description": "**We start 000!**\nWe will begin with a Quiz, and after roughly 20 min we go over to a Dance!",
                      "location":    "HP: Magic Awakened ឵឵(Sphinx)",
                      "footer":   '''"Place your right hand on my waist and...\nOne, two, three... One, two, three..."''',
                      "account":     "Prof. McGonagall",}
        
        await set_event_and_notification(server, event_info, event_duration=(1,0,0), start_time=(19,30,0), today=today)
    
    else:
        trigger_club_event.change_value(to=True)



# game midnight reminder:
@tasks.loop(time=time_trigger["game_midnight"])
async def game_midnight_reminder(server):
    today = datetime.now(tz=pytz.timezone("Africa/Cairo"))
    print(f'''"Game Midnight" task running... {datetime.now(tz=timezone.utc)}!''', today)

    delta = datetime(year=today.year, month=today.month, day=today.day) - ExtraVariable(name="base_date_maintenance").value
    if (test_bot["test_tasks"] or delta.days % 14 == 0):
        print("It's Maintenance! Notify!")

        event_info = {"image_id":    "maintenance_image",
                      "title":       "",
                      "subtitle":    "Reminder: <Maintenance!>",
                      "description": "**It starts 000!**\nDuring this period the game will be unavailable!",
                      "location":    "HP: Magic Awakened ឵឵(Sphinx)",
                      "footer":   '''"Go on, scram! Or I will hanging you by your thumbs in the dungeons!"''',
                      "account":     "Mr. Filch",}
        
        await set_event_and_notification(server, event_info, event_duration=(3,0,0), start_time=(24,0,0), today=today+timedelta(days=1))



# midnight reminders
@tasks.loop(time=time_trigger["midnight"])
async def midnight_reminder(server):
    today = datetime.now(tz=timezone.utc)
    print(f'''"Midnight" task running... {today}!''')

    # for staff on sunday
    if (test_bot["test_tasks"] or today.weekday() == 6):
        print("It's Sunday! Notify!")
        channel = server.get_channel(channel_ids["staffroom"])
        
        embed = Embed(color=system_embed_color, description="Dear Staff,\nremember to take a picture of this week's top 3 students!\n\n(Please post the screenshots below!)")
        embed.set_footer(text='''"But be quick! It is not wise to be wandering around this late hour."''')
        
        await send_webhook(target_channel=channel, user_name="Prof. Dumbledore", content="Mention: <@&1221884134121668648> <@&1221910705318662154>", embed=embed)



def convert_to_unix_time(date: datetime, mode: str):
    # get a tuple of the date attributes
    date_tuple = (date.year, date.month, date.day, date.hour, date.minute, date.second)

    # convert to unix time
    return f'<t:{int(time_module.mktime(datetime(*date_tuple).timetuple()))}:{mode}>'


async def set_event_and_notification(server, event_info, event_duration, start_time, today):
    global delete_after
    
    # for testing
    if test_bot["test_tasks"]:
        beginning = now + timedelta(minutes=after_minutes*2)
        ending    = beginning + timedelta(minutes=after_minutes)
        duration  = f"~{after_minutes} minutes"
    else:
        delete_after["hours"]   = event_duration[0] + (start_time[0] - today.hour)
        delete_after["minutes"] = event_duration[1] + (start_time[1] - today.minute)
        delete_after["seconds"] = event_duration[2] + (start_time[2] - today.second)
        
        delete_after = {key:(value if value > 0 else 0) for key,value in delete_after.items()}
        
        beginning = today.replace(hour  =(start_time[0] % 24),
                                  minute=(start_time[1] % 60),
                                  second=(start_time[2] % 60),)
        
        ending = beginning + timedelta(hours=event_duration[0], minutes=event_duration[1], seconds=event_duration[2])
        
        duration = f"~{event_duration[0]} hour{'s' if event_duration[0] > 1 else ''}"
    
    print("h:", delete_after["hours"], " m:", delete_after["minutes"], " s:", delete_after["seconds"])

    # get alternative title and insert timer
    if not event_info["title"]:
        event_name = re.search('<(.*)>', event_info["subtitle"]).group(1)
        event_info["subtitle"] = event_info["subtitle"].replace("<", "").replace(">", "")
    else:
        event_name = event_info["title"]
   
    event_info["description"] = event_info["description"].replace("000", convert_to_unix_time(date=beginning.astimezone(), mode="R"))
    
    
    # get image
    channel = server.get_channel(channel_ids["assets"])
    message = [message async for message in channel.history(limit=None) if message.content == event_info["image_id"]][0]


    if not test_bot["test_tasks"]:
        # create event
        try:
            await server.create_scheduled_event(name=event_name,
                                                start_time=beginning.astimezone(),
                                                end_time=ending.astimezone(),
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
    embed.add_field(name="Scheduled for", value=f"{convert_to_unix_time(date=beginning.astimezone(), mode='t')}", inline=True)
    embed.add_field(name="Duration", value=duration, inline=True)

    if event_info["footer"]:
        embed.set_footer(text=event_info["footer"])

    channel = server.get_channel(channel_ids["announcements"])
    message = await send_webhook(target_channel=channel, user_name=event_info["account"], content="Mention: <@&1278844289694171260>", embed=embed)

    if not test_bot["test_tasks"]:
        await message.delete(delay=delete_after["hours"]*3600+delete_after["minutes"]*60+delete_after["seconds"])