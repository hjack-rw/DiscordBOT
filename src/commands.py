import src.variables as vars

from src.body import bot
from src.db_classes import *
from src.functions import CustomHousecup, standard_response, send_webhook, get_avatar, draw_infocard, create_leaderboard, print_portkey, parse_portkey_data, print_house_members
from src.tasks import print_notification
from src.views import *

from datetime import datetime, timedelta
from itertools import chain
from typing import Optional, Literal

import statistics

from discord.embeds import Embed
from discord.errors import NotFound
from discord.interactions import Interaction
from discord.member import Member
from discord.message import Message


# SETTINGS
# for testing
# vars.test_bot["test_command"] = True # overwrite if needed

if vars.test_bot["test_command"]:
    channel_ids = vars.channel_ids_test
else:
    channel_ids = vars.channel_ids


# DB functionality
@bot.tree.command(name="backup_db")
@standard_response(silent=True)
async def backup_db(interaction:Interaction):
    ''' Backup the Database manually '''

    DB = bot.db
    DB.backup()

    await interaction.response.send_message("The Database was **backed up**!", ephemeral=True)

@bot.tree.command(name="restore_db")
@standard_response(silent=True)
async def restore_db(interaction:Interaction):
    ''' Restore the Database from backup '''

    DB = bot.db
    DB.restore()

    await interaction.response.send_message("The Database was **restored**!", ephemeral=True)

############################################################################################################

# Event functionality
@bot.tree.command(name="postpone")
@standard_response(silent=True)
async def postpone_club_event_24h(interaction:Interaction):
    ''' Postpone the next Club Event by 24h '''
    
    trigger_club_events = ExtraVariable(name="trigger_club_events")

    # change the variable value
    trigger_club_events.change(to=not trigger_club_events.get())

    await interaction.response.send_message(f"The next Club Event will be **{'restored' if trigger_club_events.get() else 'skipped'}**!", ephemeral=True)


@bot.tree.command(name="set_maintenance")
@standard_response(silent=True)
async def set_maintenance_base_date(interaction:Interaction, month:Literal[tuple(vars.months.keys())], day:int): # type: ignore
    ''' Set the Base Date for Maintenance '''

    new_date=datetime(year=datetime.now().year, month=vars.months[month], day=day)

    base_date_maintenance = ExtraVariable(name="base_date_maintenance")

    # change the variable value
    base_date_maintenance.change(to=new_date)

    await interaction.response.send_message(f"The next Maintenance will trigger **every two weeks** from **{new_date.strftime('%d/%m/%Y')}**", ephemeral=True)


@bot.tree.command(name="add_disciplines")
@standard_response()
async def add_disciplines(interaction:Interaction):
    ''' Add House Cup disciplines '''

    REQUIRED_OPTIONS = 4
    options = list(vars.housecup_disciplines_names.values())

    all_picked = []
    for idx in range(1, REQUIRED_OPTIONS+1):
        view = DropdownView(options)
        message = await interaction.channel.send(content=f"Pick the {idx}. discipline:", view=view)
        await view.wait()

        # dropdown list gets smaller with each picked option
        picked = view.picked
        all_picked.append(picked)
        
        # remove the display version of the picked item
        try:
            options.remove(vars.housecup_disciplines_names[picked])
        
        # already popped or not found — possibly due to fallback
        except ValueError:
            continue
        
        await message.delete()
    
    ExtraVariable(name="housecup_disciplines").change(to=tuple(all_picked))

############################################################################################################

# Webhook functionality
@bot.tree.command(name="polyjuice")
@standard_response()
async def send_as(interaction:Interaction, member:Optional[Member], option:Optional[Literal[tuple(vars.custom_avatars.keys())]], say:str): # type: ignore
    ''' Send a message as User '''
    
    if (member and not option) or (not member and option):
        user_name = member.nick if member else option
        user_avatar_url = get_avatar(member, none=True)

        await send_webhook(target_channel=interaction.channel, user_name=user_name, user_avatar_url=user_avatar_url, content=say)
    elif member and option:
        raise Exception("pick either a 'member' or an 'option', not both")
    else:
        raise Exception("pick a 'member' or an 'option'")

@bot.tree.command(name="send_notification")
@standard_response()
async def send_notification(interaction:Interaction, event:Literal[tuple(vars.notification_dict().keys())], member:Optional[Member], same_day:Optional[bool]=False): # type: ignore
    ''' Send the notification manually '''

    SERVER = bot.server
    today = datetime.now()

    variables = []
    if event == "Welcome" or event == "Birthday":
        if member is None:
            return await interaction.followup.send(f"{event} notifications require to select a Member!", ephemeral=True)
        else:
            if event == "Welcome":
                image = draw_infocard(new_user=member, all_members_count=len([member for member in SERVER.members if not member.bot]))
                view = WelcomeView(user=member, stickers=SERVER.stickers)
                
                variables += [member, image, view]
            elif event == "Birthday":
                variables.append([member.id])
    
    elif event == "Housecup":
        housecup_disciplines = ExtraVariable(name="housecup_disciplines")
        housecup_reset = ExtraVariable(name="housecup_reset")
        
        today = today.astimezone(tz=vars.gameserver_timezone)
        delta = datetime(year=today.year, month=today.month, day=today.day, tzinfo=vars.gameserver_timezone) - vars.base_housecup_date
        
        discipline = housecup_disciplines.get()[int(delta.days / 14) % 4]
        variables.append(discipline)

    message = await print_notification(SERVER, event_name=event, date=today, variables=variables, is_task=False, same_day=same_day)

    if not vars.test_bot["test_command"]: 
        if event == "Welcome":
            WelcomeMessages().add(user_id=member.id, message_id=message.id, date=datetime.now())
        elif event == "Housecup":
            if housecup_disciplines.get()[3] == discipline:
                housecup_reset.change(to=True)

############################################################################################################

# Portkey handling functionality
@bot.tree.context_menu(name="Accept Portkey")
@standard_response()
async def accept_portkey(interaction:Interaction, message:Message):
    ''' Accept Portkey '''
    
    SERVER = bot.server
    Portkeys().add(server=SERVER, message=message)


@bot.tree.command(name="accept_portkey")
@standard_response()
async def accept_portkey_for_user(interaction:Interaction, message_id:str, member:Member):
    ''' Accept Portkey for User '''
    
    SERVER  = bot.server

    try:
        message = await interaction.channel.fetch_message(message_id)
        Portkeys().add(server=SERVER, message=message, user_id=member.id)
    except NotFound:
        raise Exception("what you are trying to accept is not a Portkey")


@bot.tree.command(name="post_portkey")
@standard_response()
async def post_portkey(interaction:Interaction, portkey_id:str="last"):
    ''' Print a Portkey '''

    SERVER = bot.server
    CHANNEL = SERVER.get_channel(channel_ids["portkey-arrival"])

    if (portkey := Portkeys(id=portkey_id)).raw_data:
        portkey_values = portkey.get()

        if portkey_values["message_id"] is None:
            member = SERVER.get_member(portkey_values["user_id"])

            message = await CHANNEL.send(embed=print_portkey(member, portkey_values))
            portkey.unarchive(message_id=message.id)
        else:
            raise Exception("the Portkey was already UNARCHIVED")
    else:
        raise Exception("there is no Portkey with that ID")


@bot.tree.context_menu(name="Edit Portkey")
@standard_response()
async def edit_portkey(interaction:Interaction, message:Message):
    ''' Edit Portkey '''

    SERVER = bot.server

    # check if message is sent by webhook and if it has the correct embed
    if (message.author.id == vars.bot_id) and ("Portkey" in message.embeds[0].footer.text):
        if portkey_values := Portkeys(message_id=message.id).get():
            member = SERVER.get_member(portkey_values["user_id"])
            
            await message.edit(embed=print_portkey(member, portkey_values))
        else:
            await message.delete()
    
    elif message.author.id == 952824326766333972:
        raise Exception("the Portkey you are trying to edit has not yet been accepted")
    else:
        raise Exception("what you are trying to edit is not a Portkey")

############################################################################################################

# Leaderboard functionality
@bot.tree.command(name="update_lb")
@standard_response()
async def update_leaderboard(interaction: Interaction, mention_all:bool=True, with_custom_housecup:bool=True):
    ''' Updates the Server's Leaderboard '''

    SERVER  = bot.server
    CHANNEL = SERVER.get_channel(channel_ids["leaderboard"])

    # get leaderboard info
    if data := ExperienceInfo(extended=True, archived=False, order=["xp-"]).get(multiple=True):

        # clear the channel
        await CHANNEL.purge(limit=None)

        custom_housecup = []

        # post custom housecup
        if with_custom_housecup:
            custom_housecup_message = await CHANNEL.send(content="", embed=Embed(title="The leading house is... ", color=vars.system_embed_color))

            houses_names = set(list(vars.houses)[:-1])
            custom_housecup = [CustomHousecup(house=role.name, all_members_count=len(role.members)) for role in SERVER.roles if role.name in houses_names]
        
        leaderboard, custom_housecup = create_leaderboard(SERVER, data, custom_housecup)

        # post leaderboard
        for position in leaderboard:
            user_id, color, file = position
            
            embed = Embed(color=color)
            embed.set_image(url=f"attachment://{file.filename}")

            await CHANNEL.send(content="", embed=embed, file=file)

            if mention_all:
                await CHANNEL.send(content=f"<@{user_id}>")
        
        # find winning house
        if with_custom_housecup:
            all_points = list(chain.from_iterable([house.points for house in custom_housecup]))

            mean = statistics.mean(all_points)
            sd   = statistics.stdev(all_points)
            
            scoreboard = {house.name:house.for_scoreboard(mean, sd) for house in custom_housecup}

            print(scoreboard)
            winning_house = max(custom_housecup, key=lambda house: scoreboard.get(house.name, float('-inf'))).name
            
            custom_housecup_embed = custom_housecup_message.embeds[0]
            custom_housecup_embed.title += f"\n {winning_house.capitalize()} !!!"
            custom_housecup_embed.set_thumbnail(url=vars.houses[winning_house]["crest"])

            await custom_housecup_message.edit(content="", embed=custom_housecup_embed)

@bot.tree.command(name="tweak_xp")
@standard_response(silent=True)
async def tweak_xp_manually(interaction: Interaction, member:Member, action:Literal["Add", "Subtract", "Set"]="Add", amount:int=10, comment:Optional[str]=None):
    ''' Add / Subtract / Set  XP for User '''

    SERVER          = bot.server
    CHANNEL         = SERVER.get_channel(channel_ids["points-log"])
    USER_EXPERIENCE = bot.user_experience

    action = action.lower()
    current_xp = await USER_EXPERIENCE.tweak(server=SERVER, member=member, amount=amount, after_action=action.lower())

    if current_xp:
        if action != "set":
            action += "ed"
            log = f"**{member.nick or member.global_name}** - {amount} points {action}! Current XP: **{current_xp}**"
        else:
            log = f"**{member.nick or member.global_name}** - points set! XP: **{amount}**"

        if comment:
            log += f"\nComment: {comment}"

        await interaction.response.send_message(f"User {member.nick or member.global_name} has been **{action}**!", ephemeral=True)
        await CHANNEL.send(content=log)

@bot.tree.command(name="reset_xp")
@standard_response(silent=True)
async def reset_xp(interaction: Interaction, member:Member):
    ''' Reset XP for User '''
    
    SERVER  = bot.server
    CHANNEL = SERVER.get_channel(channel_ids["points-log"])

    USER_EXPERIENCE = bot.user_experience
    USER_EXPERIENCE.reset(user_id=member.id)

    await interaction.response.send_message(f"User {member.nick or member.global_name} has been **reseted**!", ephemeral=True)
    await CHANNEL.send(content=f"**{member.nick or member.global_name}** - points reseted! XP: **0**")

@bot.tree.command(name="change_lb")
@standard_response(silent=True)
async def change_leaderboard(interaction: Interaction, member:Member, username:Optional[str], offset:Optional[bool]):
    ''' Change the Leaderboard properties for User '''
    
    options = {}
    if username is None and offset is None:
        raise Exception("pick a 'username' or an 'offset'")
    
    if username and username.strip() != "":
        options["username"] = username
    if offset is not None:
        options["offset"] = offset

    USER_EXPERIENCE = bot.user_experience
    if USER_EXPERIENCE.get(user_id=member.id):
        ExperienceInfo(user_id=member.id).change(**options)

    await interaction.response.send_message(f"User {member.nick or member.global_name} leaderboard card has been **changed**!", ephemeral=True)

############################################################################################################

# User commands
@bot.tree.command(name="house_members")
@standard_response(silent=True)
async def house_members(interaction:Interaction):
    ''' Prints a list of members of each House, that will be deleted after 5 min '''
    
    SERVER  = bot.server
    MINUTES = 5

    message = await interaction.channel.send(content="", embed=print_house_members(SERVER.members, page=0, filter=0), delete_after=60*MINUTES)
    await message.edit(view=MemberView(SERVER.members, message, is_command=True))

@bot.tree.command(name="change_nickname")
@standard_response(silent=True)
async def change_nick(interaction:Interaction, nick:str):
    ''' Change your Nickname on Discord to the one in game '''

    await interaction.user.edit(nick=nick)
    await interaction.response.send_message("Your Nickname should have now **changed**!", ephemeral=True)

@bot.tree.command(name="is_house_cup_this_week")
@standard_response(silent=True)
async def is_housecup_this_week(interaction:Interaction):
    ''' Informs you if there will be a House Cup this week '''

    today = datetime.now(tz=vars.gameserver_timezone)
    today = today.replace(hour=0,
                          minute=0,
                          second=0,
                          microsecond=0,)
    
    housecup_disciplines_names = vars.housecup_disciplines_names
    disciplines = ExtraVariable(name="housecup_disciplines").get()

    trigger = False

    if (delta := (today - vars.base_housecup_date).days  % (14*4) - 1) > 50:    
        trigger = True
        discipline = disciplines[0]
        text = "New Season!\nThe schedule hasn't been released yet."
    else:
        dates, text = [today - timedelta(days=delta)], []
        for idx in range(4):
            if idx != 0:
                dates.append(dates[-1] + timedelta(days=14))
            text.append(f"{idx+1}. **{housecup_disciplines_names[disciplines[idx]]}** - {dates[-1].strftime('%d/%m/%Y')}\n")
        
        if today.weekday() != 6:
            next_saturday = today + timedelta(days=5-today.weekday())

            try:
                discipline = disciplines[dates.index(next_saturday)]
                trigger = True
            except ValueError:
                pass

    embed = Embed(color=vars.system_embed_color, description="".join(text))
    
    if trigger:
        await interaction.response.send_message(f"**YES**, there will be **{housecup_disciplines_names[discipline]}** House Cup this week!", embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message("There's **NO** House Cup this week!", embed=embed, ephemeral=True)
