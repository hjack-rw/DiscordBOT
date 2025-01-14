from src.body import bot
from src.db_classes import ExtraVariable, Portkeys
from src.functions import standard_response, send_command, send_webhook, get_avatar, print_portkey, parse_portkey_data
from src.tasks import housecup_disciplines_names
from src.variables import test_bot, server_id, bot_id, channel_ids, channel_ids_test, custom_avatars, system_embed_color, base_housecup_date
from src.views import DropdownView

from datetime import datetime, timedelta, timezone
from typing import Optional, Literal

import re
import statistics

from discord.embeds import Embed
from discord.errors import NotFound
from discord.interactions import Interaction
from discord.member import Member
from discord.message import Message


# SETTINGS
# for testing
# test_bot["test_command"] = True # overwrite if needed

if test_bot["test_command"]:
    channel_ids = channel_ids_test


# Complete list at:
# https://harrypotter.fandom.com/wiki/List_of_creatures
animal_rank = {0:  "Flobberworm", #100
               1:  "Cornish Pixie", #255
               2:  "Bowtruckle", #475
               3:  "Puffskein", #770
               4:  "Diricawl", #1150
               5:  "Kneazle", #1625
               6:  "Mooncalf", #2205
               7:  "Niffler", #2900
               8:  "Demiguise", #3720
               9:  "Yeti", #4675
               10: "Thunderbird", #5775
               11: "Sphinx", #7030
               12: "Erumpent", #8450
               13: "Graphorn", #10045
               14: "Hippogriff", #11825
               15: "Kelpie", #13800
               16: "Unicorn", #15980
               17: "Zouwu", #18375
               18: "Basilisk", #20995
               19: "Phoenix", #23850
               20: "Dragon" #26950
              }

max_level = len(animal_rank) - 1

custom_housecup = {"gryffindor": {"points": [], "all_members": 0, "link": "https://static.wikia.nocookie.net/pottermore/images/1/16/Gryffindor_crest.png/revision/latest?cb=20111112232412"},
                   "hufflepuff": {"points": [], "all_members": 0, "link": "https://static.wikia.nocookie.net/pottermore/images/5/5e/Hufflepuff_crest.png/revision/latest?cb=20111112232427"},
                   "ravenclaw":  {"points": [], "all_members": 0, "link": "https://static.wikia.nocookie.net/pottermore/images/4/40/Ravenclaw_Crest_1.png/revision/latest?cb=20140604194505"},
                   "slytherin":  {"points": [], "all_members": 0, "link": "https://static.wikia.nocookie.net/pottermore/images/4/45/Slytherin_Crest.png/revision/latest?cb=20111112232353"},}

months ={"01|January": 1, "02|February": 2, "03|March": 3, "04|April": 4, "05|May": 5, "06|June": 6, "07|July": 7, "08|August": 8, "09|September": 9, "10|October": 10, "11|November": 11, "12|December": 12}

numbers = {0: "0️⃣", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣"}

# Leaderboard functionality
def limit(value, limit):
    return value if value else limit

def get_exp(user_level, total_exp):
    return sum([(5 * (lvl ** 2) + (50 * lvl) + 100) for lvl in range(user_level)]) if total_exp else (5 * (user_level ** 2) + (50 * user_level) + 100)

def get_user_exp(current_level, percent):    
    return get_exp(current_level, total_exp=False)*percent/100 + get_exp(current_level, total_exp=True)


@bot.tree.command(name="update_lb")
async def update_leaderboard(interaction: Interaction, mention_all:bool, with_housecup:bool):
    ''' Updates the Server's Leaderboard '''
    
    await standard_response(interaction)

    server = bot.get_guild(server_id)
    channel = server.get_channel(channel_ids["leaderboard"])
    side_channel = server.get_channel(channel_ids["leaderboard_side"])

    try:
        send_command(target_channel_id=channel_ids["leaderboard_side"], app_id=1035970092284002384, version=1240001014564913213, id=1035972545276555395, command="rank", options=[{"type":6, "name":"user", "value":385899007991480321},{"type":5, "name":"showoff", "value":False}])

        # clear all channels
        await channel.purge(limit=None)
        await side_channel.purge(limit=None)

        # get leaderboard info
        page = 0
        while len([message async for message in side_channel.history(limit=None) if message.author.id == 1035970092284002384]) == page:
            print("waiting...")

            page += 1
            send_command(target_channel_id=channel_ids["leaderboard_side"], app_id=1035970092284002384, version=1240001014564913214, id=1071163634492919920,  command="leaderboard", options=[{"type":4, "name":"page", "value":page}, {"type":5, "name":"show_off", "value":True}])

            if test_bot["test_command"]:
                break
        
        user_ids = []
        for message in [message async for message in side_channel.history(limit=None) if message.author.id == 1035970092284002384][::-1]:
            user_ids += re.findall(r'''\<@\s*\+?(-?\d+)\s*\>''', message.content)

        await side_channel.purge(limit=None)

        # post housecup
        if with_housecup:
            house_embed = Embed(title="The leading house is...", color=system_embed_color)
            house_message = await channel.send(content="", embed=house_embed)

        # post leaderboard info
        for idx, user in enumerate(user_ids, 1):
            send_command(target_channel_id=channel_ids["leaderboard_side"], app_id=1035970092284002384, version=1240001014564913213, id=1035972545276555395, command="rank", options=[{"type":6, "name":"user", "value":user},{"type":5, "name":"showoff", "value":True}])

            while len([message async for message in side_channel.history(limit=None)]) != idx:
                print("waiting...")

                if test_bot["test_command"]:
                    break
        
            last_message = [message async for message in side_channel.history(limit=1)][0]
                    
            member = server.get_member(int(user))

            progress = last_message.attachments[0]
            level = int(re.findall(pattern=r'''l\s*\+?(-?\d+)\s\(''', string=progress.description)[0])

            percent = int(re.findall(pattern=r'''\s*\+?(-?\d+)%''', string=progress.description)[0])
            exp = get_user_exp(level, percent)

            roles = [role.name for role in member.roles]
            custom_housecup[[house for house in custom_housecup if house in roles][0]]["points"] += [exp]

            if level > max_level:
                level = max_level

            animal_string = f'''{member.display_name}'{"s" if (member.display_name[-1].upper() != "S") else ""} pet rank is:  {animal_rank[level]}'''

            if member.roles[-1].name in ["captain", "moderator", "co-captain", "captain (cross guild)", "co-captain (cross guild)"]:
                color = member.roles[-1].color.value
            else:
                color = 5198940


            embed = Embed(title=animal_string, color=color)
            embed.set_image(url=progress.url)

            await channel.send(content="", embed=embed)
            if mention_all:
                await channel.send(content=f"<@{user}>")

            if test_bot["test_command"]:
                break


        if with_housecup:
            for role in server.roles:
                if role.name in [house for house in custom_housecup]:
                    custom_housecup[role.name]["all_members"] = len(role.members)
            
            all_points = sum([value["points"] for _, value in custom_housecup.items()], [])
            mean = statistics.mean(all_points)
            sd = statistics.stdev(all_points) if not test_bot["test_command"] else 0
            
            scoreboard = {}
            for key,value in custom_housecup.items():
                points = [point for point in value["points"] if (point >= mean - 2*sd) and (point <= mean + 2*sd)]
                
                active_members = len(points) if not test_bot["test_command"] else 1
                scoreboard[key] = sum(points) / active_members / limit(value=value["all_members"], limit=1)

            winning_house = max(custom_housecup, key=scoreboard.get)
            
            print(scoreboard)

            house_embed = house_message.embeds[0]
            house_embed.title = f"The leading house is... {winning_house.capitalize()}!"
            house_embed.set_image(url=custom_housecup[winning_house]["link"])

            await house_message.edit(content="", embed=house_embed)
    
        print("done")
    
    except ValueError as error:
        await interaction.channel.send("Something went very wrong here... a server restart might be in order!", delete_after=10)
        print(error)
    
    except IndexError as error:
        await interaction.channel.send("Something went very wrong here... check the Experienced source leaderboard!", delete_after=10)
        print(error)


# Webhook functionality
@bot.tree.command(name="polyjuice")
async def send_as(interaction:Interaction, member:Optional[Member], option:Optional[Literal[tuple(custom_avatars.keys())]], say:str): # type: ignore
    ''' Send a message as User '''
    
    if not member and not option:
        await interaction.response.send_message("Pick a member or an option!", ephemeral=True)

    else:
        await standard_response(interaction)

        if member:
            user_name = member.nick
            user_avatar_url = get_avatar(member)
        else:
            user_name = option
            user_avatar_url = None

        try:
            await send_webhook(target_channel=interaction.channel, user_name=user_name, user_avatar_url=user_avatar_url, content=say)
        except ValueError as error:
            print(error)


# Event handling functionality
@bot.tree.command(name="postpone")
async def postpone_club_event_24h(interaction:Interaction):
    ''' Postpone the next Club Event by 24h '''
    
    trigger_club_events = ExtraVariable(name="trigger_club_events")

    if trigger_club_event_value := trigger_club_events.get():
        await interaction.response.send_message("The next Club Event will be **skipped**!", ephemeral=True)
    else:
        await interaction.response.send_message("The next Club Event will be **restored**!", ephemeral=True)
    
    # change the variable value
    trigger_club_events.change(to=not trigger_club_event_value)


@bot.tree.command(name="set_maintenance")
async def set_maintenance_base_date(interaction:Interaction, month:Literal[tuple(months.keys())], day:int): # type: ignore
    ''' Set the base date for Maintenance '''

    today = datetime.now()
    
    base_date_maintenance = ExtraVariable(name="base_date_maintenance")
    
    try:
        new_date=datetime(year=today.year, month=months[month], day=day)
        await interaction.response.send_message(f"The next Maintenance will trigger **every two weeks** from **{new_date.strftime('%d/%m/%Y')}**", ephemeral=True)
    
        # change the variable value
        base_date_maintenance.change(to=new_date)

    except ValueError as error:
        await interaction.response.send_message(f"Something went very wrong here... {error}!", ephemeral=True)


# Portkey handling functionality
@bot.tree.context_menu(name="Accept Portkey")
async def accept_portkey(interaction:Interaction, message:Message):
    ''' Accept Portkey '''
    
    await standard_response(interaction)

    try:
        server = bot.get_guild(server_id)
        portkey = parse_portkey_data(server, message)
        Portkeys().add(portkey)
        
    except ValueError as error:
        await interaction.channel.send(f"Something went very wrong here... {error}!", delete_after=10)


@bot.tree.command(name="accept_portkey")
async def accept_portkey_for_user(interaction:Interaction, message_id:str, member:Member):
    ''' Accept Portkey for User '''
    
    await standard_response(interaction)

    try:
        server = bot.get_guild(server_id)
        message = await interaction.channel.fetch_message(message_id)
        portkey = parse_portkey_data(server, message, member)
        Portkeys().add(portkey)
    
    except ValueError as error:
        await interaction.channel.send(f"Something went very wrong here... {error}!", delete_after=10)
    
    except NotFound:
        await interaction.channel.send("Something went very wrong here... what you are trying to accept is not a Portkey!", delete_after=10)


@bot.tree.command(name="post_portkey")
async def post_portkey(interaction:Interaction, id:str):
    ''' Print a Portkey '''

    await standard_response(interaction)

    server = bot.get_guild(server_id)

    try:
        portkey = Portkeys(id).get()
        channel = server.get_channel(channel_ids["portkey-arrival"])
        
        await channel.send(embed=print_portkey(server, portkey))
    except IndexError:
        await interaction.channel.send("Something went very wrong here... there is no Portkey with that ID!", delete_after=10)


@bot.tree.context_menu(name="Edit Portkey")
async def edit_portkey(interaction:Interaction, message:Message):
    ''' Edit Portkey '''

    await standard_response(interaction)

    # check if message is sent by webhook and if it has the correct embed
    if (message.author.id == bot_id) and ("Portkey" in message.embeds[0].footer.text):
        id = int(message.embeds[0].footer.text.split("#")[1])

        server = bot.get_guild(server_id)
        portkey = Portkeys(id).get()

        await message.edit(embed=print_portkey(server, portkey))
    
    elif message.author.id == 952824326766333972:
        await interaction.channel.send("Something went very wrong here... the Portkey you are trying to edit has not yet been accepted!", delete_after=10)
    else:
        await interaction.channel.send("Something went very wrong here... what you are trying to edit is not a Portkey!", delete_after=10)
    

@bot.tree.command(name="add_disciplines")
async def add_disciplines(interaction:Interaction):
    ''' Add House Cup disciplines '''

    await standard_response(interaction)

    required_options = 4
    
    options = list(housecup_disciplines_names.values())

    all_picked = []
    for idx in range(1, required_options+1):
        view = DropdownView(options)
        message = await interaction.channel.send(content=f"Pick the {idx}. discipline:", view=view)
        await view.wait()

        all_picked.append(view.picked)

        # dropdown list gets smaller with each picked option
        if len(all_picked) != idx:
            all_picked.append(options.pop())
        else:
            options.remove(housecup_disciplines_names[all_picked[-1]])
        
        await message.delete()
    
    ExtraVariable(name="housecup_disciplines").change(to=tuple(all_picked))


@bot.tree.command(name="is_house_cup_this_week")
async def is_housecup_this_week(interaction:Interaction):
    ''' Informs you if there will be a House Cup this week '''

    today = datetime.now(tz=timezone.utc)

    if (today.weekday() == 6):
        trigger = False
    else:
        next_saturday = datetime(year=today.year, month=today.month, day=today.day) + timedelta(days=5-today.weekday())
        
        delta = next_saturday - (base_housecup_date + timedelta(days=1))
        if trigger := (delta.days % 14 == 0):
            housecup_disciplines = ExtraVariable(name="housecup_disciplines")
            discipline = housecup_disciplines.get()[int(delta.days / 14) % 4]
    
    if trigger:
        await interaction.response.send_message(f"**YES**, there will be **{housecup_disciplines_names[discipline]}** House Cup this week!", ephemeral=True)
    else:
        await interaction.response.send_message("There's **NO** House Cup this week!", ephemeral=True)