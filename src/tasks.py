from src.db_classes import ExtraVariable, Portkeys
from src.functions import send_webhook, replace_multiple, get_image
from src.variables import test_bot, channel_ids, channel_ids_test, system_embed_color, wait_for, gameserver_timezone, main_timezone, base_housecup_date

from datetime import datetime, time, timedelta

import re
import time as time_module

from discord.app_commands.errors import CommandInvokeError
from discord.embeds import Embed
from discord.enums import EntityType, PrivacyLevel
from discord.ext import tasks


__all__ = ["morning_reminder", "weekly_cards_reminder", "housecup_reminder", "club_events_reminder", "game_midnight_reminder", "midnight_reminder", "create_a_task"] 


time_trigger = {"game_reset":    time(hour=4,  minute=0,  second=0, tzinfo=gameserver_timezone), # UTC+2 - 03:00 - exact
                "morning":       time(hour=7,  minute=0,  second=0, tzinfo=main_timezone),       # UTC+1 - 08:00 - exact
                "weekly_cards":  time(hour=16, minute=59, second=0, tzinfo=gameserver_timezone), # UTC+2 - 16:00 - exact
                "housecup":      time(hour=19, minute=0,  second=0, tzinfo=gameserver_timezone), # UTC+2 - 18:00 - 24 h early
                "club_events":   time(hour=19, minute=25, second=0, tzinfo=main_timezone),       # UTC+1 - 20:30 - 5 min early
                "game_midnight": time(hour=23, minute=0,  second=0, tzinfo=gameserver_timezone), # UTC+2 - 23:00 - 1 h early
                "midnight":      time(hour=23, minute=0,  second=0, tzinfo=main_timezone),}      # UTC+1 - 24:00 - 1 h early

def notification_dict(is_short=False):
    dict = {"Welcome": "event",
            "Birthday": "morning",
            "Card - Matagot": "weekly_cards",
            "Card - Book of Monsters": "weekly_cards",
            "Card - Cornish Pixies": "weekly_cards",
            "Housecup": "housecup",
            "Club Events": "club_events",
            "Club Points": "club_events",
            "Maintenance": "game_midnight",
            "Rankings": "midnight",}
    
    if is_short:
        dict["Weekly Cards"] = "weekly_cards" 
        return {key:value for key,value in dict.items() if key in ["Weekly Cards", "Housecup", "Club Events", "Maintenance"]}
    return dict

delete_after = {"hours":0, "minutes":0, "seconds":0}

weekdays = {0:"Monday", 1:"Tuesday", 2:"Wednesday", 3:"Thursday", 4:"Friday", 5:"Saturday", 6:"Sunday"}
months   = {"01|January": 1, "02|February": 2, "03|March": 3, "04|April": 4, "05|May": 5, "06|June": 6, "07|July": 7, "08|August": 8, "09|September": 9, "10|October": 10, "11|November": 11, "12|December": 12}

housecup_disciplines_names = {0: "Best Partners",
                              1: "Dance Club",
                              2: "Top Wizard",
                              3: "History of Magic",
                              4: "Muggle Studies",
                              5: "Casual Matches",
                              6: "Qudditch",}


# SETTINGS
# for testing
#test_bot["test_tasks"] = True # overwrite if needed

if test_bot["test_tasks"]:
    now = datetime.now()
    after_minutes = wait_for
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
#    today = datetime.now(tz=time_trigger["game_reset"].tzinfo)


# morning reminder:
@tasks.loop(time=time_trigger["morning"])
async def morning_reminder(server):
    today = datetime.now(tz=time_trigger["morning"].tzinfo)

    if not test_bot["test_tasks"]:
        birthdays = Portkeys(message_id="unarchived", birthday=datetime(year=2000, month=today.month, day=today.day), specified_columns=["message_id", "birthday", "user_id"]).get(multiple=True)
    else:
        birthdays = [385899007991480321 for _ in range(1)]

    # trigger on someone birthday
    if birthdays:
        await print_notification(server, date=today, event_name="Birthday", variables=[birthdays])


# weekly_cards reminder:
@tasks.loop(time=time_trigger["weekly_cards"])
async def weekly_cards_reminder(server):
    today = datetime.now(tz=time_trigger["weekly_cards"].tzinfo)

    # trigger on monday, wednesday and friday
    if not test_bot["test_tasks"]:
        if today.weekday() == 0:
            await print_notification(server, date=today, event_name="Card - Matagot")
        
        elif today.weekday() == 2:
            await print_notification(server, date=today, event_name="Card - Book of Monsters")
        
        elif today.weekday() == 4:
            await print_notification(server, date=today, event_name="Card - Cornish Pixies")
    
    else:
        await print_notification(server, date=today, event_name="Card - Matagot")
        await print_notification(server, date=today, event_name="Card - Book of Monsters")
        await print_notification(server, date=today, event_name="Card - Cornish Pixies")


# housecup reminder:
@tasks.loop(time=time_trigger["housecup"])
async def housecup_reminder(server):
    today = datetime.now(tz=time_trigger["housecup"].tzinfo)

    housecup_disciplines = ExtraVariable(name="housecup_disciplines")
    housecup_reset = ExtraVariable(name="housecup_reset")

    # trigger every 2 weeks from base date
    delta = datetime(year=today.year, month=today.month, day=today.day, tzinfo=gameserver_timezone) - base_housecup_date
    if (test_bot["test_tasks"] or delta.days % 14 == 0):
        discipline = housecup_disciplines.get()[int(delta.days / 14) % 4]

        await print_notification(server, date=today, event_name="Housecup", variables=[discipline])

        if (not test_bot["test_tasks"] and housecup_disciplines.get()[3] == discipline):
            housecup_reset.change(to=True)

    # reset to default (0, 1, 2, 3)    
    elif (delta.days % 14 == 2 and housecup_reset.get()):
        housecup_disciplines.change(to=(0, 1, 2, 3))
        housecup_reset.change(to=False)


# club_events reminder:
@tasks.loop(time=time_trigger["club_events"])
async def club_events_reminder(server):
    today = datetime.now(tz=time_trigger["club_events"].tzinfo)

    # trigger every workday
    if (test_bot["test_tasks"] or today.weekday() not in [5, 6]):
        
        # and if variable is True
        trigger_club_events = ExtraVariable(name="trigger_club_events")
        if trigger_club_events.get():
            await print_notification(server, date=today, event_name="Club Events")
        
        # default True
        else:
            trigger_club_events.change(to=True)
    
    # trigger every weekend
    if (test_bot["test_tasks"] or today.weekday() in [4, 6]):
        
        # delete the previous ones
        if not test_bot["test_tasks"]:
            channel = server.get_channel(channel_ids["announcements"])
            [await message.delete() async for message in channel.history(after=(today - timedelta(days=2))) if (message.author.name == "Prof. Snape" and message.content == "Mention: <@&1314983531050569828>")]
        
        message = await print_notification(server, date=today, event_name="Club Points")
        
        # if it is Sunday delete it after reset
        if not test_bot["test_tasks"] and today.weekday() == 6:
            next_reset = today.replace(hour  =time_trigger["game_reset"].hour,
                                       minute=time_trigger["game_reset"].minute,
                                       second=time_trigger["game_reset"].second,
                                       tzinfo=time_trigger["game_reset"].tzinfo,) + timedelta(days=1)

            delta = next_reset - today
            await message.delete(delay=delta.seconds)


# game_midnight reminder:
@tasks.loop(time=time_trigger["game_midnight"])
async def game_midnight_reminder(server):
    today = datetime.now(tz=time_trigger["game_midnight"].tzinfo)

    # trigger every 2 weeks from base date
    delta = datetime(year=today.year, month=today.month, day=today.day) - ExtraVariable(name="base_date_maintenance").get()
    if (test_bot["test_tasks"] or delta.days % 14 == 0):
        await print_notification(server, date=today, event_name="Maintenance")


# midnight reminders
@tasks.loop(time=time_trigger["midnight"])
async def midnight_reminder(server):
    today = datetime.now(tz=time_trigger["midnight"].tzinfo)

    # trigger on sunday (FOR STAFF ONLY!)
    if (test_bot["test_tasks"] or today.weekday() == 6):        
        await print_notification(server, date=today, event_name="Rankings")



# user create task
def create_a_task(timer):

    @tasks.loop(hours=timer["hours"], minutes=timer["minutes"], seconds=timer["seconds"], count=2)
    async def task_template(event_info):
        if task_template.current_loop != 0:
            print(f"Task executed! {event_info} {datetime.now()}")
        else:
            task_template.__name__ = f"task_{event_info['id']}"

    return task_template



def catch_error(dict:dict):
    for key in ["extra_fields", "title", "subtitle", "thumbnail"]:
        try:
            dict[key]
        except KeyError:
            dict[key] = None
    else:
        return dict


async def print_notification(server, date, event_name, variables=[], is_task=True, same_day=False):
    events = notification_dict()
    task = events[event_name]

    if is_task:
        if test_bot["test_tasks"] and event_name not in ["Welcome", "Card - Book of Monsters", "Card - Cornish Pixies", "Club Points"]:
            print(f'''"{task}" task running... {datetime.now()}!''')
    else:
        try:
            date = date.astimezone(tz=time_trigger[task].tzinfo)
        except KeyError:
            pass

    file, view = None, None

    if event_name == "Welcome":
        new_user, file, view = variables
        
        channel = server.get_channel(channel_ids["welcome"])

        event_info = {"mention":    f"Mention: <@{new_user.id}>",
                      "title":      f"Welcome, {new_user.name}, to GatesOfPurgatory! <:hugs:1256225688403447888>",
                      "description": "Go to <id:guide> and follow the instructions :)",
                      "footer":   f'''"You are a Wizard, {new_user.name}."''',
                      "account":     "Prof. Hagrid",}
        
        embed = Embed(title=f"Welcome, {new_user.name}, to GatesOfPurgatory! <:hugs:1256225688403447888>",  description="Go to <id:guide> and follow the instructions :)", color=system_embed_color)


    elif event_name == "Birthday":
        birthdays = variables[0]
        
        channel = server.get_channel(channel_ids["the-3-broomsticks"])

        event_info = {"mention":       "Mention: @everyone",
                      "subtitle":      "Birthday Announcement!",
                      "description":  f"**GOP  •  {date.strftime('%d/%m/%Y')}**\nPlease, wish <@{birthdays[0]}> a **Happy Birthday** <:hugs:1256225688403447888> :heart:",
                      "extra_fields":[f"Wait! There is more...\nPlease, wish <@{birthday}> a **Happy Birthday** as well <:hugs:1256225688403447888> :heart:" for birthday in birthdays[1:]],
                      "thumbnail":     "https://i.pinimg.com/564x/d8/48/59/d848592fca62cc100b148b5b77006248.jpg",
                      "footer":     '''"I can see something in the stars...\nToday is a very special day!"''',
                      "account":       "Prof. Trelawney",}


    elif task == "weekly_cards":
        link = "https://discord.com/channels/1221838993071538327/1278363571083804777/000"

        event_info = {"subtitle":       "Reminder: Weekly <Free Card>!",
                      "description": f'''Map: {link}\nGo to the **001** and click on the 002 003!\n\nPick the option: **"004"**!\nYou will get 005 of the card.''',
                      "footer":      '''"Swish and flick everyone!\nJust like we have been practicing..."''',
                      "account":        "Prof. Flitwick",}

        if event_name == "Card - Matagot":
            event_info["image_id"] = "card_1_image"
            event_info["title"] = "<Matagot! (rare)>"
            
            event_info["description"] = event_info["description"].replace("/000", "/1278841345133252662")
            event_info["description"] = replace_multiple(event_info["description"], ["Staircase", "\nMatagot", "next to the Transfiguration Classroom", "Hand it Over to Hagrid", "1 copy"])
        
        elif event_name == "Card - Book of Monsters":
            event_info["image_id"] = "card_2_image"
            event_info["title"] = "<Book of Monsters! (rare)>"

            event_info["description"] = event_info["description"].replace("/000", "/1278841654739992588")
            event_info["description"] = replace_multiple(event_info["description"], ["History of Magic Classroom", "Book", "in the corner", "Stroke the Spine and Then Open It", "1 copy"])
            
        elif event_name == "Card - Cornish Pixies":
            event_info["image_id"] = "card_3_image"
            event_info["title"] = "<Cornish Pixies! (common)>"
            
            event_info["description"] = event_info["description"].replace("/000", "/1278842175886590078")
            event_info["description"] = replace_multiple(event_info["description"], ["Library", "Pixies", "first bookcase row left", "Use Glacius.", "3 copies"])

        return await set_event_and_notification(server, event_info, date, event_duration=(4,0,0), start_time=(17,0,0))


    elif event_name == "Housecup":
        discipline = variables[0]
        
        event_info = {"image_id":    "housecup_image",
                      "title":      f"<{housecup_disciplines_names[discipline]}!>",
                      "subtitle":    "Reminder: <House Cup>!",
                      "description": "Make sure you be there and may the best house win!",
                      "footer":   '''"Did you put your name for the House Cup yet?!" he asked calmly.''',
                      "account":     "Prof. Dumbledore",}
        
        return await set_event_and_notification(server, event_info, date, time_delta=(0 if same_day else 1), event_duration=(2,0,0), start_time=(19,0,0), only_hour=False)


    elif event_name == "Club Events":
        event_info = {"image_id":    "event_image",
                      "title":       "GOP Club Events!",
                      "subtitle":   f"Reminder: {weekdays[date.weekday()]}!",
                      "description": "**We start 000!**\nWe will begin with a Quiz, and after roughly 20 min we go over to a Dance!",
                      "footer":   '''"Place your right hand on my waist and...\nOne, two, three... One, two, three..."''',
                      "account":     "Prof. McGonagall",}
        
        return await set_event_and_notification(server, event_info, date, event_duration=(1,0,0), start_time=(19,30,0))


    elif event_name == "Club Points":
        channel = server.get_channel(channel_ids["announcements"])

        event_info = {"mention":     "Mention: <@&1314983531050569828>",
                      "description": "Reminder to all who haven't earned\ntheir 100 Club points yet!\n\n"\
                                     "Please do so by the **end of the week**\nor inform a <@&1221884134121668648> / <@&1221910705318662154>\nif you are unable to do so!",
                      "footer":   '''"And be warned... I shall know if you have not practiced."''',
                      "account":     "Prof. Snape",}


    elif event_name == "Maintenance":
        event_info = {"image_id":    "maintenance_image",
                      "title":       "",
                      "subtitle":    "Reminder: <Maintenance!>",
                      "description": "**It starts 000!**\nDuring this period the game will be unavailable!",
                      "footer":   '''"Go on, scram! Or I will hanging you by your thumbs in the dungeons!"''',
                      "account":     "Mr. Filch",}
        
        return await set_event_and_notification(server, event_info, date, time_delta=(0 if same_day else 1), event_duration=(3,0,0), start_time=(24,0,0))


    elif event_name == "Rankings":
        channel = server.get_channel(channel_ids["staffroom"])

        event_info = {"mention":     "Mention: <@&1221884134121668648> <@&1221910705318662154>",
                      "description": "Dear Staff,\nremember to take a picture of this week's top 3 students!\n\n(Please post the screenshots below!)",
                      "footer":   '''"But be quick! It is not wise to be wandering around this late hour."''',
                      "account":     "Prof. Dumbledore",}
    
    
    event_info = catch_error(event_info)

    embed = Embed(color=system_embed_color, title=event_info["title"], description=event_info["description"])

    if event_info["subtitle"]:
        embed.set_author(icon_url="https://storage.googleapis.com/chronicle-assets/images/icons/bell-alert-white.png", name=event_info["subtitle"])

    if event_info["extra_fields"]:
        for field in event_info["extra_fields"]:
            embed.add_field(name="", value=field, inline=False)

    if event_info["thumbnail"]:
        embed.set_thumbnail(url=event_info["thumbnail"])
    
    embed.set_footer(text=event_info["footer"])

    if file:
        embed.set_image(url=f"attachment://{file.filename}")
    
    return await send_webhook(target_channel=channel, user_name=event_info["account"], content=event_info["mention"], embed=embed, file=file, view=view)



def convert_to_unix_time(date:datetime, mode:str):
    
    # get a tuple of the date attributes
    date_tuple = (date.year, date.month, date.day, date.hour, date.minute, date.second)

    # convert to unix time
    return f'<t:{int(time_module.mktime(datetime(*date_tuple).timetuple()))}:{mode}>'


async def set_event_and_notification(server, event_info, date, event_duration, start_time, only_hour=True, time_delta=0):
    global delete_after
    
    trigger_day = date
    if time_delta:
        trigger_day += timedelta(days=time_delta)
    
    # for testing
    if test_bot["test_tasks"]:
        beginning = now + timedelta(minutes=after_minutes*2)
        ending    = beginning + timedelta(minutes=after_minutes)
        duration  = f"~{after_minutes} minutes"
    else:
        delete_after["hours"]   = event_duration[0] + (start_time[0] - trigger_day.hour)   + (time_delta * 24)
        delete_after["minutes"] = event_duration[1] + (start_time[1] - trigger_day.minute)
        delete_after["seconds"] = event_duration[2] + (start_time[2] - trigger_day.second)
        
        beginning = trigger_day.replace(hour  =(start_time[0] % 24),
                                        minute=(start_time[1] % 60),
                                        second=(start_time[2] % 60),)
        
        ending = beginning + timedelta(hours=event_duration[0], minutes=event_duration[1], seconds=event_duration[2])
        
        duration = f"~{event_duration[0]} hour{'s' if event_duration[0] > 1 else ''}"
    
    print("h:", delete_after["hours"], " m:", delete_after["minutes"], " s:", delete_after["seconds"])

    # get alternative title and insert timer
    if not event_info["title"]:
        event_name = re.search('<(.*)>', event_info["subtitle"]).group(1)
        event_info["subtitle"] = replace_multiple(event_info["subtitle"], [("<", ""), (">", "")], self_idx=False)

    elif ("<" in event_info["title"]) and (">" in event_info["title"]):
        event_name = re.search('<(.*)>', event_info["subtitle"]).group(1) + f": {re.search('<(.*)>', event_info['title']).group(1)}"
        event_info["title"] = replace_multiple(event_info["title"], [("<", ""), (">", "")], self_idx=False)
        event_info["subtitle"] = replace_multiple(event_info["subtitle"], [("<", ""), (">", "")], self_idx=False)
    else:
        event_name = event_info["title"]
   
    event_info["description"] = event_info["description"].replace("000", convert_to_unix_time(date=beginning.astimezone(), mode="R"))
    
    try:
        event_info["location"]
    except KeyError:
        event_info["location"] = "HP: Magic Awakened ឵឵(Sphinx)"

    
    # get image
    channel = server.get_channel(channel_ids["assets"])
    message = [message async for message in channel.history(limit=None) if message.content == event_info["image_id"]][0]


    if not test_bot["test_tasks"]:

        # create event
        try:
            await server.create_scheduled_event(name=event_name,
                                                start_time=beginning.astimezone() if beginning > date else (date + timedelta(minutes=2)).astimezone(),
                                                end_time=ending.astimezone(),
                                                description=event_info["description"],
                                                location=event_info["location"],
                                                privacy_level=PrivacyLevel.guild_only,
                                                entity_type=EntityType.external,
                                                image=get_image(url=message.attachments[0]))
        except ValueError:
            print("Could not create event... Image not found!")
        except CommandInvokeError:
            print("Could not create event... Bad time!")
    
    
    # create notification message
    embed = Embed(color=system_embed_color, title=event_info["title"], description=event_info["description"])
    embed.set_author(icon_url="https://storage.googleapis.com/chronicle-assets/images/icons/bell-alert-white.png", name=event_info["subtitle"])
    embed.add_field(name="Location", value=event_info["location"], inline=False)
    embed.add_field(name="Scheduled for", value=f"{convert_to_unix_time(date=beginning.astimezone(), mode=('t' if only_hour else 'f'))}", inline=True)
    embed.add_field(name="Duration", value=duration, inline=True)

    if event_info["footer"]:
        embed.set_footer(text=event_info["footer"])

    channel = server.get_channel(channel_ids["announcements"])
    message = await send_webhook(target_channel=channel, user_name=event_info["account"], content="Mention: <@&1278844289694171260>", embed=embed)

    if not test_bot["test_tasks"]:
        await message.delete(delay=(delete_after["hours"]*3600)+(delete_after["minutes"]*60)+delete_after["seconds"])