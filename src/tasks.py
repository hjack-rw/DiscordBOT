import src.variables as vars

from src.db_classes import ExtraVariable, Portkeys
from src.functions import get_today, print_notification

from datetime import datetime, time, timedelta

from discord.ext import tasks


__all__ = ["morning_reminder", "weekly_cards_reminder", "housecup_reminder", "club_events_reminder", "game_midnight_reminder", "midnight_reminder", "create_a_task"] 


# SETTINGS
# for testing
# vars.test_bot["test_tasks"] = True # overwrite if needed

if vars.test_bot["test_tasks"]:
    now = datetime.now()

    # replace time
    hour, minute  = (int(value) for value in now.strftime("%H/%M").split("/"))
    if minute <= (59 - vars.wait_for):
        minute += vars.wait_for
    else:
        hour += 1
        minute = (minute + vars.wait_for) % 60
    tz = now.astimezone().tzinfo

    time_trigger = {key:time(hour=hour, minute=minute, tzinfo=tz) for key in vars.time_trigger}
    channel_ids = vars.channel_ids_test
    
    del[hour, minute, tz]
else:
    channel_ids = vars.channel_ids
    time_trigger = vars.time_trigger



# game reset reminder:
#@tasks.loop(time=time_trigger["game_reset"])
#async def game_reset_reminder(server):
#    today = datetime.now(tz=time_trigger["game_reset"].tzinfo)


# morning reminder:
@tasks.loop(time=time_trigger["morning"])
@get_today()
async def morning_reminder(bot, today):
    DB = bot.db
    SERVER = bot.get_guild(vars.server_id)
    
    if not vars.test_bot["test_tasks"]:
        birthdays = Portkeys(message_id="unarchived", birthday=datetime(year=2000, month=today.month, day=today.day), specified_columns=["user_id", "message_id", "birthday"]).get(multiple=True)
    else:
        birthdays = [385899007991480321 for _ in range(1)]

    # trigger on someone birthday
    if birthdays:
        await print_notification(SERVER, date=today, event_name="Birthday", variables=[birthdays])
    
    try:
        DB.backup()
    except Exception as error:
        print("task error, " + error)


# weekly_cards reminder:
@tasks.loop(time=time_trigger["weekly_cards"])
@get_today()
async def weekly_cards_reminder(server, today):
    
    # trigger on monday, wednesday and friday
    if not vars.test_bot["test_tasks"]:
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
@get_today()
async def housecup_reminder(server, today):
    housecup_disciplines = ExtraVariable(name="housecup_disciplines")
    housecup_reset = ExtraVariable(name="housecup_reset")

    # trigger every 2 weeks from base date
    delta = datetime(year=today.year, month=today.month, day=today.day, tzinfo=vars.gameserver_timezone) - vars.base_housecup_date
    if (vars.test_bot["test_tasks"] or delta.days % 14 == 0):
        discipline = housecup_disciplines.get()[int(delta.days / 14) % 4]

        await print_notification(server, date=today, event_name="Housecup", variables=[discipline])

        if (not vars.test_bot["test_tasks"] and housecup_disciplines.get()[3] == discipline):
            housecup_reset.change(to=True)

    # reset to default (0, 1, 2, 3)    
    elif (delta.days % 14 == 2 and housecup_reset.get()):
        housecup_disciplines.change(to=(0, 1, 2, 3))
        housecup_reset.change(to=False)


# club_events reminder:
@tasks.loop(time=time_trigger["club_events"])
@get_today()
async def club_events_reminder(server, today):

    # trigger every workday
    if (vars.test_bot["test_tasks"] or today.weekday() not in [5, 6]):
        
        # and if variable is True
        trigger_club_events = ExtraVariable(name="trigger_club_events")
        
        if trigger_club_events.get():
            await print_notification(server, date=today, event_name="Club Events")
        
        # default True
        else:
            trigger_club_events.change(to=True)
    
    # trigger every weekend
    if (vars.test_bot["test_tasks"] or today.weekday() in [4, 6]):
        
        # delete the previous ones
        if not vars.test_bot["test_tasks"]:
            channel = server.get_channel(channel_ids["announcements"])
            [await message.delete() async for message in channel.history(after=(today - timedelta(days=2))) if (message.author.name == "Prof. Snape" and message.content == "Mention: <@&1314983531050569828>")]
        
        message = await print_notification(server, date=today, event_name="Club Points")
        
        # if it is Sunday delete it after reset
        if not vars.test_bot["test_tasks"] and today.weekday() == 6:
            next_reset = today.replace(hour  =time_trigger["game_reset"].hour,
                                       minute=time_trigger["game_reset"].minute,
                                       second=time_trigger["game_reset"].second,
                                       tzinfo=time_trigger["game_reset"].tzinfo,) + timedelta(days=1)

            delta = next_reset - today
            await message.delete(delay=delta.seconds)


# game_midnight reminder:
@tasks.loop(time=time_trigger["game_midnight"])
@get_today()
async def game_midnight_reminder(server, today):

    # trigger every 2 weeks from base date
    delta = datetime(year=today.year, month=today.month, day=today.day) - ExtraVariable(name="base_date_maintenance").get()
    if (vars.test_bot["test_tasks"] or delta.days % 14 == 0):
        await print_notification(server, date=today, event_name="Maintenance")


# midnight reminders
@tasks.loop(time=time_trigger["midnight"])
@get_today()
async def midnight_reminder(server, today):
    
    # trigger on sunday (FOR STAFF ONLY!)
    if (vars.test_bot["test_tasks"] or today.weekday() == 6):        
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