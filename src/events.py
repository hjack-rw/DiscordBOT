from src.body import bot
from src.db_classes import WelcomeMessages, Portkeys
from src.functions import draw_infocard, parse_xp_amount, print_notification
from src.variables import test_bot, channel_sections_ids, channel_ids, channel_ids_test
from src.views import WelcomeView

from datetime import datetime
from math import ceil
from random import randint
from time import time

# SETTINGS
# for testing
# test_bot["test_events"] = True # overwrite if needed

if test_bot["test_events"]:
    channel_ids = channel_ids_test


# Enter Server
@bot.event
async def on_member_join(member):
    MEMBERS_VIEW = bot.members_view

    # skip bots
    if not member.bot:
        SERVER = bot.server

        image = draw_infocard(new_user=member, all_members_count=len([member for member in SERVER.members if not member.bot]))
        view = WelcomeView(user=member, stickers=SERVER.stickers)

        message = await print_notification(SERVER, event_name="Welcome", variables=[member, image, view])

        if not test_bot["test_events"]:
            WelcomeMessages().add(user_id=member.id, message_id=message.id, date=datetime.now())
    
        await MEMBERS_VIEW.update_members(members=SERVER.members)
    
    else:
        print(f"BOT: {member.name} joined the server!")


# Leave Server
@bot.event
async def on_member_remove(member):
    SERVER          = bot.server
    MEMBERS_VIEW    = bot.members_view
    USER_EXPERIENCE = bot.user_experience

    await MEMBERS_VIEW.update_members(members=SERVER.members)
    
    if not test_bot["test_events"]:
        
        CHANNEL = SERVER.get_channel(channel_ids["portkey-arrival"])
        if message_id := Portkeys(user_id=member.id).archive():
            
            message = await CHANNEL.fetch_message(message_id)
            await message.delete()

        CHANNEL = SERVER.get_channel(channel_ids["welcome"])
        if message_id := WelcomeMessages().remove(user_id=member.id):
            
            message = await CHANNEL.fetch_message(message_id)
            await message.delete()
        
        try:
            USER_EXPERIENCE.archive(user_id=member.id)
        except Exception:
            pass


# Post on Server
@bot.event
async def on_message(message):
    SERVER             = bot.server
    USER_EXPERIENCE    = bot.user_experience
    USER_LAST_EXECUTED = bot.user_last_executed
    MESSAGE_COOLDOWN   = 60.0
    
    # skip bots
    if message.author.bot:
        return
    
    # skip if message channel is not allowed
    if message.channel.category and message.channel.category.id not in [channel_sections_ids["general"], channel_sections_ids["guides"], channel_sections_ids["offtopic"]]:
        return

    else:
        now = time()
        last_time = USER_LAST_EXECUTED.get(message.author.id, 0)

        # assert cooldown
        if now - last_time < MESSAGE_COOLDOWN:
            return
        
        # add xp (random xp (15-25) + length * 0.02)     
        xp_gained = randint(15, 25) + ceil(len(message.content) / 50)
        
        try:
            await USER_EXPERIENCE.tweak(server=SERVER, member=message.author, amount=xp_gained)
        except Exception as error:
            print(str(error))


#@bot.event
#async def on_reaction_add(reaction, user):
#    message = reaction.message
