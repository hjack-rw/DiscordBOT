from src.body import bot
from src.db_classes import ExtraVariable, WelcomeMessages, Portkeys
from src.functions import CustomHousecup, standard_response, send_webhook, get_avatar, draw_infocard, get_csv, create_leaderboard, print_portkey, parse_portkey_data, print_house_members
from src.tasks import notification_dict, months, housecup_disciplines_names, print_notification
from src.variables import test_bot, server_id, bot_id, channel_ids, channel_ids_test, custom_avatars, houses, system_embed_color, gameserver_timezone, base_housecup_date
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
# test_bot["test_command"] = True # overwrite if needed

if test_bot["test_command"]:
    channel_ids = channel_ids_test


# Leaderboard functionality
@bot.tree.command(name="update_lb")
async def update_leaderboard(interaction: Interaction, mention_all:bool, with_custom_housecup:bool, url:str):
    ''' Updates the Server's Leaderboard '''

    await standard_response(interaction)

    server = bot.get_guild(server_id)
    channel = server.get_channel(channel_ids["leaderboard"])

    try:
        # get leaderboard info
        data = sorted(get_csv(url),key=lambda x: x["xp"], reverse=True)

        # clear the channel
        await channel.purge(limit=None)

        custom_housecup = []

        # post custom housecup
        if with_custom_housecup:
            custom_housecup_message = await channel.send(content="", embed=Embed(title="The leading house is... ", color=system_embed_color))

            houses_names = list(houses.keys())[:-1]
            
            for role in server.roles:
                if role.name in houses_names:
                    custom_housecup += [CustomHousecup(house=role.name, all_members_count=len(role.members))]
        
        leaderboard, custom_housecup = create_leaderboard(server, data, custom_housecup)

        # post leaderboard
        for position in leaderboard:
            user_id, color, file = position
            
            embed = Embed(color=color)
            embed.set_image(url=f"attachment://{file.filename}")

            await channel.send(content="", embed=embed, file=file)

            if mention_all:
                await channel.send(content=f"<@{user_id}>")
        
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
            custom_housecup_embed.set_thumbnail(url=houses[winning_house]["crest"])

            await custom_housecup_message.edit(content="", embed=custom_housecup_embed)

    except ValueError as error:
        await interaction.channel.send(f"Something went very wrong here... {error}!", delete_after=10)


# Event functionality
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

    base_date_maintenance = ExtraVariable(name="base_date_maintenance")
    
    try:
        new_date=datetime(year=datetime.now().year, month=months[month], day=day)
        await interaction.response.send_message(f"The next Maintenance will trigger **every two weeks** from **{new_date.strftime('%d/%m/%Y')}**", ephemeral=True)
    
        # change the variable value
        base_date_maintenance.change(to=new_date)

    except ValueError as error:
        await interaction.response.send_message(f"Something went very wrong here... {error}!", ephemeral=True)


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

    today = datetime.now(tz=gameserver_timezone)
    today = today.replace(hour=0,
                          minute=0,
                          second=0,
                          microsecond=0,)
    
    disciplines = ExtraVariable(name="housecup_disciplines").get()

    trigger = False

    if (delta := (today - base_housecup_date).days  % (14*4) - 1) > 50:    
        trigger = True
        discipline = disciplines[0]
        text = "New Season!\nThe schedule hasn't been released yet."
    else:
        dates, text = [today - timedelta(days=delta)], []
        for idx in range(4):
            if idx != 0:
                dates += [dates[-1] + timedelta(days=14)]
            text += [f"{idx+1}. **{housecup_disciplines_names[disciplines[idx]]}** - {dates[-1].strftime('%d/%m/%Y')}\n"]
        
        if today.weekday() != 6:
            next_saturday = today + timedelta(days=5-today.weekday())

            try:
                discipline = disciplines[dates.index(next_saturday)]
                trigger = True
            except ValueError:
                pass

    embed = Embed(color=system_embed_color, description="".join(text))
    
    if trigger:
        await interaction.response.send_message(f"**YES**, there will be **{housecup_disciplines_names[discipline]}** House Cup this week!", embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message("There's **NO** House Cup this week!", embed=embed, ephemeral=True)


@bot.tree.command(name="send_notification")
async def send_notification(interaction:Interaction, event:Literal[tuple(notification_dict().keys())], member:Optional[Member], same_day:Optional[bool]): # type: ignore
    ''' Send the notification manually '''
    
    await standard_response(interaction)

    server = bot.get_guild(server_id)
    today = datetime.now()

    variables = []
    if event == "Welcome" or event == "Birthday":
        if member is None:
            return await interaction.followup.send(f"{event} notifications require to select a Member!", ephemeral=True)
        else:
            if event == "Welcome":
                image = draw_infocard(new_user=member, all_members=len([member for member in server.members if not member.bot]))
                view = WelcomeView(user=member, stickers=server.stickers)
                
                variables += [member, image, view]
            elif event == "Birthday":
                variables.append([member.id])
    elif event == "Housecup":
        housecup_disciplines = ExtraVariable(name="housecup_disciplines")
        housecup_reset = ExtraVariable(name="housecup_reset")
        
        today = today.astimezone(tz=gameserver_timezone)
        delta = datetime(year=today.year, month=today.month, day=today.day, tzinfo=gameserver_timezone) - base_housecup_date
        
        discipline = housecup_disciplines.get()[int(delta.days / 14) % 4]
        variables.append(discipline)

    message = await print_notification(server, date=today, event_name=event, is_task=False, variables=variables, same_day=same_day)

    if not test_bot["test_command"]: 
        if event == "Welcome":
            WelcomeMessages().add(user_id=member.id, message_id=message.id, date=datetime.now())
        elif event == "Housecup":
            if housecup_disciplines.get()[3] == discipline:
                housecup_reset.change(to=True)


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
async def post_portkey(interaction:Interaction, portkey_id:str):
    ''' Print a Portkey '''

    await standard_response(interaction)

    server = bot.get_guild(server_id)

    try:
        channel = server.get_channel(channel_ids["portkey-arrival"])
        portkey = Portkeys(id=portkey_id, message_id="archived")
        
        if portkey_values := portkey.get():
            message = await channel.send(embed=print_portkey(server, portkey_values))
            portkey.unarchive(message_id=message.id)
        else:
            await interaction.channel.send("Something went very wrong here... the Portkey was already UNARCHIVED!", delete_after=10)

    except IndexError:
        await interaction.channel.send("Something went very wrong here... there is no Portkey with that ID!", delete_after=10)


@bot.tree.context_menu(name="Edit Portkey")
async def edit_portkey(interaction:Interaction, message:Message):
    ''' Edit Portkey '''

    await standard_response(interaction)

    # check if message is sent by webhook and if it has the correct embed
    if (message.author.id == bot_id) and ("Portkey" in message.embeds[0].footer.text):
        server = bot.get_guild(server_id)

        if portkey_values := Portkeys(message_id=message.id).get():
            await message.edit(embed=print_portkey(server, portkey_values))
        else:
            await message.delete()
    
    elif message.author.id == 952824326766333972:
        await interaction.channel.send("Something went very wrong here... the Portkey you are trying to edit has not yet been accepted!", delete_after=10)
    else:
        await interaction.channel.send("Something went very wrong here... what you are trying to edit is not a Portkey!", delete_after=10)


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


# User commands
@bot.tree.command(name="house_members")
async def house_members(interaction:Interaction):
    ''' Prints a list of members of each House, that will be deleted after 5 min '''
    
    await standard_response(interaction)
    minutes = 5
    
    server = bot.get_guild(server_id)

    message = await interaction.channel.send(content="", embed=print_house_members(server.members, page=0, filter=0), delete_after=60*minutes)
    await message.edit(view=MemberView(server.members, message, is_command=True))


@bot.tree.command(name="change_nickname")
async def change_nick(interaction:Interaction, nick:str):
    ''' Change your Nickname on Discord to the one in game '''

    await standard_response(interaction)
    await interaction.user.edit(nick=nick)