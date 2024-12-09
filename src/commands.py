from src.body import bot
from src.functions import send_command, send_webhook, get_avatar
from src.variables import local_deploy, server_id, channel_ids, system_embed_color

import re
import statistics

import discord

from discord.embeds import Embed
from discord.interactions import Interaction


# SETTINGS 
test_command = True if local_deploy else False
#// test_command = True # an overwrite


# for testing
if test_command:
    channel_ids = {key:channel_ids["testing"] for key in channel_ids}


# Complete list at:
# https://harrypotter.fandom.com/wiki/List_of_creatures
animal_rank = {0: "Flobberworm", #100
               1: "Cornish Pixie", #255
               2: "Bowtruckle", #475
               3: "Puffskein", #770
               4: "Diricawl", #1150
               5: "Kneazle", #1625
               6: "Mooncalf", #2205
               7: "Niffler", #2900
               8: "Demiguise", #3720
               9: "Yeti", #4675
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

house_cup = {"gryffindor": {"points": [], "all_members": 0, "link": "https://static.wikia.nocookie.net/pottermore/images/1/16/Gryffindor_crest.png/revision/latest?cb=20111112232412"},
             "hufflepuff": {"points": [], "all_members": 0, "link": "https://static.wikia.nocookie.net/pottermore/images/5/5e/Hufflepuff_crest.png/revision/latest?cb=20111112232427"},
             "ravenclaw":  {"points": [], "all_members": 0, "link": "https://static.wikia.nocookie.net/pottermore/images/4/40/Ravenclaw_Crest_1.png/revision/latest?cb=20140604194505"},
             "slytherin":  {"points": [], "all_members": 0, "link": "https://static.wikia.nocookie.net/pottermore/images/4/45/Slytherin_Crest.png/revision/latest?cb=20111112232353"},}



# Leaderboard functionality
def limit(value, limit):
    return value if value else limit

def get_exp(user_level, total_exp):
    return sum([(5 * (lvl ** 2) + (50 * lvl) + 100) for lvl in range(user_level)]) if total_exp else (5 * (user_level ** 2) + (50 * user_level) + 100)

def get_user_exp(current_level, percent):    
    return get_exp(current_level, total_exp=False)*percent/100 + get_exp(current_level, total_exp=True)


@bot.tree.command(name="update_lb")
async def update_leaderboard(interaction: Interaction, mention_all:bool, with_house_cup:bool):
    ''' Updates the Server's Leaderboard '''
    await interaction.response.send_message("A wizard must show patience: please, wait for it to finish!", ephemeral=True)

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

            if test_command:
                break
        
        user_ids = []
        for message in [message async for message in side_channel.history(limit=None) if message.author.id == 1035970092284002384][::-1]:
            user_ids += re.findall(r"\<@\s*\+?(-?\d+)\s*\>", message.content)

        await side_channel.purge(limit=None)

        # post house cup
        if with_house_cup:
            house_embed = Embed(title="The leading house is...", color=system_embed_color)
            house_message = await channel.send(content="", embed=house_embed)

        # post leaderboard info
        for idx, user in enumerate(user_ids, 1):
            send_command(target_channel_id=channel_ids["leaderboard_side"], app_id=1035970092284002384, version=1240001014564913213, id=1035972545276555395, command="rank", options=[{"type":6, "name":"user", "value":user},{"type":5, "name":"showoff", "value":True}])

            while len([message async for message in side_channel.history(limit=None)]) != idx:
                print("waiting...")

                if test_command:
                    break
        
            last_message = [message async for message in side_channel.history(limit=1)][0]
                    
            member = server.get_member(int(user))

            progress = last_message.attachments[0]
            level = int(re.findall(pattern=r'''l\s*\+?(-?\d+)\s\(''', string=progress.description)[0])

            percent = int(re.findall(pattern=r'''\s*\+?(-?\d+)%''', string=progress.description)[0])
            exp = get_user_exp(level, percent)

            for house in house_cup:
                if any(role in [role.name for role in member.roles] for role in [house]):
                    house_cup[house]["points"].append(exp)

            if level > max_level:
                level = max_level

            animal_string = f'''{member.display_name}'{"s" if member.display_name[-1].upper() != "S" else ""} pet rank is:  {animal_rank[level]}'''

            if member.roles[-1].name in ["captain", "moderator", "co-captain", "captain (cross guild)", "co-captain (cross guild)"]:
                color = member.roles[-1].color.value
            else:
                color = 5198940


            embed = Embed(title=animal_string, color=color)
            embed.set_image(url=progress.url)

            await channel.send(content="", embed=embed)
            if mention_all:
                await channel.send(content=f"<@{user}>")

            if test_command:
                break


        if with_house_cup:
            for role in server.roles:
                if role.name in [house for house in house_cup]:
                    house_cup[role.name]["all_members"] = len(role.members)
            
            all_points = sum([value["points"] for _, value in house_cup.items()], [])
            mean = statistics.mean(all_points)
            sd = statistics.stdev(all_points) if not test_command else 0
            
            scoreboard = {}
            for key,value in house_cup.items():
                points = [point for point in value["points"] if (point >= mean - 2*sd) and (point <= mean + 2*sd)]
                
                active_members = len(points) if not test_command else 1
                scoreboard[key] = sum(points) / active_members / limit(value=value["all_members"], limit=1)

            winning_house = max(house_cup, key=scoreboard.get)
            
            print(scoreboard)

            house_embed = house_message.embeds[0]
            house_embed.title = f"The leading house is... {winning_house.capitalize()}!"
            house_embed.set_image(url=house_cup[winning_house]["link"])

            await house_message.edit(content="", embed=house_embed)
    
        print("done")
    
    except ValueError as error:
        await interaction.channel.send("Something went very wrong here... a server restart might be in order!", delete_after=5)
        print(error)



# Webhook functionality
@bot.tree.command(name="polyjuice")
async def send_as(interaction: Interaction, member:discord.Member, say:str):
    ''' Send message as user '''
    await interaction.response.send_message("A wizard must show patience: please, wait for it to finish!", ephemeral=True)

    try:
        await send_webhook(target_channel=interaction.channel, user_name=member.nick, user_avatar_url=get_avatar(member), content=say)
    except ValueError as error:
        print(error)