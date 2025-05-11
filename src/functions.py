from src.variables import test_bot, server_id, webhook_id, custom_avatars, houses, wait_for, absolute_path, discord_token, bot_token, system_embed_color

from datetime import datetime
from functools import reduce
from PIL import Image, ImageFont, ImageDraw, ImageFilter

import copy
import csv
import io
import json
import re
import time

import requests
session = requests.Session()

from discord.embeds import Embed
from discord.file import File
from discord.utils import MISSING


# SETTINGS
# for testing
# test_bot["test_command"] = True # overwrite if needed

headers = {"authorization": f"Bot {bot_token}",
           "content-type": "application/json",
           "user-agent": "BOT (http://discord.com, v1.0)",}

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

class CustomHousecup:
    def __init__(self, house:str, all_members_count:int):
        self.name = house
        self.all_members_count = all_members_count
        self.points = []

    def for_scoreboard(self, mean, sd):
        if not self.points:
            return 0
        
        points = [point for point in self.points if (mean - 2 * sd <= point <= mean + 2 * sd)]
           
        # sum of points / active members / all_members
        return sum(points) / max(len(points), 1) / max(self.all_members_count, 1)

form_answers = ["🤺 Solo Dueling",
                "🤺🤺 Duo Dueling",
                "😎🤺 Casual Matches",
                "🧙🌳 Club Adventures",
                "🧙🧙 Club Events (Dance / Quiz / Duel Tournament)",
                "📚 Classes",
                "🧹 Quidditch",
                "🌳 Solo Forbidden Forest",
                "🌳🌳 Team Forbidden Forest (OTP / Gold / Echos)",
                "🌹 Verdant Victories",
                "🌱 Herbology",
                "🕺💃 Dancing",
                "📸 Photoshoots",]


async def standard_response(interaction):
    await interaction.response.send_message("A wizard must show patience... please, wait for the command to finish!", ephemeral=True)

async def wait_till_posted(channel, idx):
    while len([message async for message in channel.history(limit=None)]) != idx:
        if test_bot["test_command"]:
            break
    
    print("endless loop finished!")

async def send_command(target_channel_id, app_id, version, id, command, options=[]):
    payload = {"type":2,
               "application_id":str(app_id),
               "guild_id":str(server_id),
               "channel_id":str(target_channel_id),
               "session_id":"3794653e1bf277766e6356b596fd495d",
               "data":{"version":str(version), "id":str(id), "name":command, "type":1, "options": options}}
    
    # overwrite headers
    headers = {"authorization": str(discord_token),
               "content-type": "application/json",}

    response = session.post(url="https://discord.com/api/v9/interactions", json=payload, headers=headers,)
    #print(response)

    if response.status_code < 300:
        time.sleep(wait_for)
    else:
        raise ValueError("FAILED TO SEND COMMAND!")


def change_webhook_channel(target_channel):
    payload = {"channel_id":target_channel.id}
    return session.patch(f"https://discordapp.com/api/webhooks/{webhook_id}", json=payload, headers=headers,)


async def send_webhook(target_channel, user_name, user_avatar_url=None, content="", embed=None, file=None, view=None):            

    response = change_webhook_channel(target_channel)
    #print(response)

    if user_avatar_url is None:
        try:
            user_avatar_url = custom_avatars[user_name]
        except KeyError:
            user_avatar_url = custom_avatars["Prof. Dumbledore"]

    if response.status_code == 200:
        webhook = [webhook for webhook in await target_channel.webhooks() if webhook.id == webhook_id][0]
        
        embed = embed if embed else MISSING
        file = file if file else MISSING
        view = view if view else MISSING

        return await webhook.send(content=content, username=user_name, avatar_url=user_avatar_url, embed=embed, file=file, view=view, wait=True)
    else:
        raise ValueError("FAILED TO CREATE WEBHOOK!")


def replace_multiple(string:str, replace_list:list, self_idx=True):
    if self_idx:
        for idx, instance in enumerate(replace_list):
            replace_list[idx] = (f"{idx+1}".rjust(3, "0"), instance)
    
    return reduce(lambda a, kv: a.replace(*kv), replace_list, string)


def get_json(url):
    # create HTTP response object 
    response = requests.get(url)

    try:
        return json.loads(response.content)
    except:
        raise ValueError("NO JSON FILE FOUND!")

def get_csv(url):
    # create HTTP response object 
    response = requests.get(url)
    content  = response.content.decode('utf-8').replace("\ufeff", "").splitlines()

    # TODO! make it universal
    try:
        return [{key:int(value) for key,value in row.items() if key != "_"} for row in csv.DictReader(f=content[1:], fieldnames=["_", "_", "id", "xp", "_", "_", "_", "_"])]
    except:
        raise ValueError("NO CSV FILE FOUND!")

def get_image(url):
    response = session.get(url,)
    return response.content

def get_avatar(user, none=False):
    try:
        return user.avatar._url
    except AttributeError:
        if none:
            return None
        return user.default_avatar._ur

def scale_image(base_width, image):
    x, y = image.size
    
    w_size = base_width
    w_percent = base_width / float(x)
    
    h_size = int(round(y * w_percent))
    return image.resize((w_size, h_size), Image.Resampling.LANCZOS)

def check_shape(shape):
    return [(int(round(x)), int(round(y))) for x,y in shape]

def get_position(center, image_center, offset=(0,0)):
    x, y = center
    x_off, y_off = offset
    w_size, h_size = image_center
    
    return check_shape(shape=[(x - (w_size / 2) + x_off, y - (h_size / 2) + y_off)])[0]


def draw_infocard(new_user, all_members):
    background = Image.open(absolute_path + "image_module/card_template.png")
    
    ## profile picture ##
    url = get_avatar(user=new_user)

    # download avatar
    avatar = Image.open(io.BytesIO(get_image(url=url)))
    
    # scaling
    avatar = scale_image(base_width=220, image=avatar)
    x, _ = avatar.size

    # add avatar mask
    blur_radius = 1
    avatar_mask = Image.new(mode="L", size=avatar.size, color=0)
    draw = ImageDraw.Draw(avatar_mask)
    draw.ellipse(xy=(5, 8, x-5, x-5), fill=255)
    avatar_mask = avatar_mask.filter(ImageFilter.GaussianBlur(blur_radius))

    background.paste(im=avatar, box=(215,20), mask=avatar_mask)

    draw = ImageDraw.Draw(background)


    ## text ##
    # add nickname
    if len(new_user.name) > 15:
        name_font = ImageFont.truetype(font=(absolute_path + "image_module/RUNES.ttf"), size=80)
    else:
        name_font = ImageFont.truetype(font=(absolute_path + "image_module/RUNES.ttf"), size=100)

    if len(new_user.name) > 9:
        draw.text(xy=(995,115), text=new_user.name, fill=(235,235,235), font=name_font, align="center", anchor='rm')
    else:
        draw.text(xy=(795,115), text=new_user.name, fill=(235,235,235), font=name_font, align="center", anchor='mm')
    
    # add footer
    footer_font = ImageFont.truetype(font=(absolute_path + "image_module/MAGIC.ttf"), size=35)
    draw.text(xy=(790,200), text=f"We are now {all_members} members!", fill=(235,235,235), font=footer_font, align="center", anchor='mm')

    
    ## save and return file ##
    bytes = io.BytesIO()
    background.save(bytes, format="PNG")
    bytes.seek(0)
    
    return File(bytes, filename="card.png")


def draw_leaderboard(member, rank, house, level, progress, static):
    background, profile_border, full_bar, bar_mask, marker, \
    MAGIC_font_88, MAGIC_font_45, MAGIC_font_42, RUNES_font_88, RUNES_font_75 = static
    background = copy.deepcopy(background)


    ## profile picture ##
    url = get_avatar(user=member, none=True)
    
    xy = (150, 150)

    if url is None:
        # black avatar if missing
        avatar = Image.new(mode="L", size=xy, color=0)
    else:
        # download avatar
        avatar = Image.open(io.BytesIO(get_image(url=url)))
        
        # scaling
        avatar = scale_image(base_width=xy[0], image=avatar)
    
    avatar_center = (177, 156)

    # add avatar mask
    avatar_mask = Image.new(mode="L", size=avatar.size, color=0)
    draw = ImageDraw.Draw(avatar_mask)
    draw.ellipse(xy=(0, 0, *avatar.size), fill=255)

    x, y = avatar.size
    draw.polygon(check_shape(shape=[(0,y/2), (0,y), (x,y), (x,y/2)]), fill=255)

    background.paste(im=avatar, box=get_position(center=avatar_center, image_center=avatar.size, offset=(5,8)), mask=avatar_mask)

    # add profile border
    background.alpha_composite(im=profile_border, dest=get_position(center=avatar_center, image_center=profile_border.size))

    draw = ImageDraw.Draw(background)


    ## box info ##
    # add rank
    draw.text(xy=(380, 118), text="#" + f"{rank}".rjust(3, "0"), fill=(235,235,235), font=MAGIC_font_88, align="left", anchor='lm')

    # TODO!:
    name = member.nick or member.global_name
    problem_name = {1108425644032938044:"Voodoochild", 776678540166823936:"Leil", 1132281522041401454:"BADGER", 871307021138399232:"Tam Lin", 1140274502882820116: "S i r i u s"}
    name = problem_name.pop(member.id, name.replace(" ", "\n "))

    # add nickname
    if len(name) <= 9 and ("\n" in name):
        name_font = RUNES_font_88
    else:
        name_font = RUNES_font_75

    draw.multiline_text(xy=(570, 160 if "\n" in name else 128), text=name, fill=(235,235,235), font=name_font, align="left", anchor='lm', spacing=-35)

    # add house logo
    if house:
        house_logo = Image.open(absolute_path + f"image_module/houses/{house}.png")
        background.alpha_composite(im=house_logo, dest=(388, 194))

    # progress details (pet name and level)    
    draw.text(xy=(911, 170), text=f"Pet: {animal_rank[level]}", fill=(235,235,235), font=MAGIC_font_45, align="left", anchor='lm')
    draw.text(xy=(911, 227), text=f"Level: {level}", fill=(235,235,235), font=MAGIC_font_45, align="left", anchor='lm')


    ## progress bar ##
    # limit progress
    percent = progress

    if percent < 0.05:
        percent = 0.05
    elif percent > 1:
        percent = 1

    # proportion
    bar_offset = 1480 - int(round(percent * 1480))

    progress_bar = Image.new("RGBA", full_bar.size, (0, 0, 0, 0))

    x, y = full_bar.size
    progress_bar.paste(im=full_bar.crop((bar_offset, 0, x, y)), mask=bar_mask.crop((0, 0, x-bar_offset, y)))

    # add progress bar
    background.alpha_composite(im=progress_bar)

    # add progress bar marker
    background.alpha_composite(im=marker, dest=get_position(center=(95, 322), image_center=marker.size, offset=(int(round(percent * 1480)-85), 0) if percent >= 0.059 else (0, 0)))

    # add percentage
    draw.text(xy=(x-175 if percent < 0.5 else 175, 322), text=f"{round(progress*100, 2)}%", fill=(235,235,235), font=MAGIC_font_42, align="center", anchor='mm')
    
    
    ## save and return file ##
    bytes = io.BytesIO()
    background.save(bytes, format="PNG")
    bytes.seek(0)
    
    return File(bytes, filename=f"leaderboard_{member.id}.png")


def get_level_and_progress(exp_total):
    exp = 0
    level = 0

    # Calculate current level
    while True:
        exp_for_next_level = 5 * (level ** 2) + (50 * level) + 100
        if exp + exp_for_next_level > exp_total:
            break
        exp += exp_for_next_level
        level += 1

    # Progress within the current level
    exp_into_next_level = exp_total - exp
    percent = exp_into_next_level / exp_for_next_level

    return level, percent


def create_leaderboard(server, data, custom_housecup):
    ## get static files for leaderboard ##
    # the basic template
    background = Image.open(absolute_path + "image_module/leaderboard_template.png")

    # the profile border
    profile_border = Image.open(absolute_path + "image_module/leaderboard_frogcard_template.png")
    
    # the full progress bar
    full_bar = Image.open(absolute_path + f"image_module/leaderboard_bar.png")
    
    # the mask for the begining of the bar
    bar_mask = Image.new(mode="L", size=full_bar.size, color=255)
    draw = ImageDraw.Draw(bar_mask)
    _, y = full_bar.size
    draw.polygon(check_shape(shape=[(0, 0), (0, y), (91, y), (91, 0)]), fill=0)

    # the progress bar marker
    marker = Image.open(absolute_path + f"image_module/leaderboard_bar_frog.png")

    # the fonts
    MAGIC_font_88 = ImageFont.truetype(font=(absolute_path + "image_module/MAGIC.ttf"), size=88)
    MAGIC_font_45 = ImageFont.truetype(font=(absolute_path + "image_module/MAGIC.ttf"), size=45)
    MAGIC_font_42 = ImageFont.truetype(font=(absolute_path + "image_module/MAGIC.ttf"), size=42)

    RUNES_font_88 = ImageFont.truetype(font=(absolute_path + "image_module/RUNES.ttf"), size=88)
    RUNES_font_75 = ImageFont.truetype(font=(absolute_path + "image_module/RUNES.ttf"), size=75)


    ## create loop for each user ##
    rank, leaderboard = 0, []
    for user in data:

        # get member, skip if can't
        member = server.get_member(int(user["id"]))
        if member is None:
            continue
        else:
            rank += 1

        # get member level and progress from exp
        level, progress = get_level_and_progress(user["xp"])

        # limit the levels
        if level > max_level:
            level = max_level
            progress = 1

        house = None
        roles = [role.name for role in member.roles]

        # add points for the custom housecup
        for idx, house in enumerate(custom_housecup):
            if house.name in roles:
                custom_housecup[idx].points += [user["xp"]]
                house = house.name
                break
        else:
            # get house if no custom housecup
            if house is None:
                for role in roles:
                    if role in list(houses.keys())[:-1]:
                        house = role
                        break

        # get the special role color
        if roles[-1] in ["captain", "moderator", "co-captain", "captain (cross guild)", "co-captain (cross guild)"]:
            color = member.roles[-1].color.value
        else:
            color = 5198940

        file = draw_leaderboard(member, rank, house, level, progress, static=(background, profile_border, full_bar, bar_mask, marker, 
                                                                              MAGIC_font_88, MAGIC_font_45, MAGIC_font_42, RUNES_font_88, RUNES_font_75))
        leaderboard += [(user["id"], color, file)]

        #if test_bot["test_command"]:
            #    break

    return leaderboard, custom_housecup


def get_member_id_by_nick(server, nick):
    try:
        return [member.id for member in server.members if member.nick == nick][0]
    except IndexError:
        return None

def remove_extra_characters(string, is_id=False):
    if is_id:
        return re.sub(r'''\D''', "", string)
    else:
        return replace_multiple(string.lstrip(" ").rstrip(" "), [("\r", ""), ("\n", "")], self_idx=False)
    
def parse_multiple_possibilities(value):
    if len(list := [remove_extra_characters(value) for value in value.split("|")]) == 1:
        list += [None]
    return list

def parse_portkey_data(server, message, member=None):
    if message.author.id == 952824326766333972:
        for field in message.embeds[0].fields:
            idx = field.name.split(".")[0]

            if idx == "1":
                if member is None:
                    if (user_id := get_member_id_by_nick(server, nick=field.value)) is None:
                        raise ValueError(f"no User with nickname {field.value} on the server")
                else:
                    user_id = member.id
            
            elif idx == "2":
                if not (game_id := remove_extra_characters(field.value, is_id=True)):
                    game_id = 0
                else:
                    game_id = int(game_id)
            
            elif idx == "3":
                continue
            
            elif idx == "4":
                (from_wb, old_username) = parse_multiple_possibilities(field.value)
                from_wb = True if (from_wb == "Yes") else False
            
            elif idx == "5":
                multiple_choice = parse_multiple_possibilities(field.value)
                
                additional_info = multiple_choice.pop(-1)
                
                if additional_info in form_answers:
                    multiple_choice += [additional_info]
                    additional_info = None

                multiple_choice = "".join([("1" if (answer in multiple_choice) else "0") for answer in form_answers[::-1]])
            
            elif idx == "6":
                birthday_date = field.value.split(".")
                
                if birthday_date != ["-"]:
                    birthday = datetime(day=int(birthday_date[0]), month=int(birthday_date[1]), year=2000)
                    if (year := int(birthday_date[2])-1900) == datetime.now().year-1900:
                        year = None
                else:
                    birthday, year = None, None
            
            elif idx == "7":
                extra = field.value if (field.value != "-") else None
        
        return (user_id, game_id, from_wb, old_username, multiple_choice, additional_info, birthday, year, extra)
    else:
        raise ValueError("what you are trying to accept is not a Portkey")


def print_portkey(server, portkey):
    member = server.get_member(int(portkey["user_id"]))
    
    try:
        roles = [role.name for role in member.roles]

        if member.roles[-1].name in ["captain", "moderator", "co-captain", "captain (cross guild)", "co-captain (cross guild)"]:
            color = member.roles[-1].color.value
        else:
            color = 5198940
    except AttributeError:
        color = system_embed_color

    
    doc_url = "https://docs.google.com/document/d/1CJMk8wJZkYnXG729xHGPvsyaj5BtrXMZeqlIOV_4qtA/edit?usp=sharing"
    
    form_answers_extended = [f"{answer}\n\n" for answer in form_answers]
    form_answers_extended += [f"{portkey['additional_info']}\n\n"]
    

    embed = Embed(color=color, description=f"**User:** <@{portkey['user_id']}>")
    
    line_1 = f"{member.nick or member.global_name} | `#" + f"{portkey['game_id'] if portkey['game_id'] else 0}`".rjust(10, "0") + f" [📋]({doc_url})"
    embed.add_field(name="1. Hello, I'm... | And my ID is...", value=line_1, inline=True)

    line_2 = houses[[house for house in houses if house in roles][0]]["emoji"]
    embed.add_field(name="2. My house is...", value=line_2, inline=True)
    
    line_3 = (("Yes | " if portkey["from_wb"] else "No, ") + portkey["old_username"]) if portkey["old_username"] else ("Yes" if portkey["from_wb"] else "No")
    embed.add_field(name="3. Am I from the WB server? | My name was...", value=line_3.replace(" | 0", ", "), inline=False)

    line_4 = "• " + "• ".join([form_answers_extended[idx] for idx,choice in enumerate(portkey["multiple_choice"][::-1] + ("1" if portkey["additional_info"] else "0")) if choice == "1"])
    embed.add_field(name="4. In the game I like doing...", value=line_4, inline=False)
    
    if (not_skip := portkey["birthday"] is not None):
        birthday = portkey["birthday"]
        
        if year := portkey["year"]:
            birthday = birthday.replace(year = year + 1900)

        line_5 = birthday.strftime("%d.%m.%Y") if year else birthday.strftime("%d.%m")
        embed.add_field(name="5. I was born...", value=line_5, inline=False)

    if portkey["extra"]:
        line_6 = portkey["extra"]
        embed.add_field(name=f"{6 if not_skip else 5}. You may also want to know...", value=line_6, inline=False)
    
    embed.set_footer(text=f"GOP  •  Portkey #{portkey['id']}")

    return embed


def print_house_members(members, page, filter):
    
    # filter by house and group
    house = list(houses.keys())[page]
    group = ["gop", "guest", "cross guild"][filter]

    users = []
    for member in members:
        roles = set([role.name for role in member.roles])

        # equivalent to .issubset()
        if {house, group} <= roles:
            users += [member]

    users = sorted(users, key=lambda x: (x.nick or x.global_name))
    
    for idx, user in enumerate(users):
        users[idx] = f"{idx+1}. {user.nick or user.global_name} - <@{user.id}>"

    return Embed(color=system_embed_color, title=houses[house]["emoji"], description=f"**{group.capitalize() if filter != 0 else group.upper()}:**\n"+"\n".join(users))