from src.variables import server_id, webhook_id, custom_avatars, houses, wait_for, absolute_path, discord_token, bot_token, system_embed_color

from datetime import datetime
from functools import reduce
from PIL import Image, ImageFont, ImageDraw, ImageFilter

import io
import json
import re
import time

import requests
session = requests.Session()

from discord.embeds import Embed
from discord.file import File
from discord.utils import MISSING


__all__ = ["standard_response", "send_command", "send_webhook", "replace_multiple", "get_image", "get_avatar", "draw_infocard", "get_json_info", "parse_portkey_data", "print_portkey", "print_house_members"] 


headers = {"authorization": f"Bot {bot_token}",
           "content-type": "application/json",
           "user-agent": "BOT (http://discord.com, v1.0)",}


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


async def send_webhook(target_channel, user_name, user_avatar_url=None, content="", embed=None, file=None, view=None):            
    payload = {"channel_id":target_channel.id}
    
    if user_avatar_url is None:
        try:
            user_avatar_url = custom_avatars[user_name]
        except KeyError:
            user_avatar_url = custom_avatars["Prof. Dumbledore"]
    
    response = session.patch(f"https://discordapp.com/api/webhooks/{webhook_id}", json=payload, headers=headers,)
    #print(response)

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


def get_image(url):
    response = session.get(url,)
    return response.content

def get_avatar(user):
    try:
        return user.avatar._url
    except AttributeError:
        return user.default_avatar._url

def draw_infocard(new_user, all_members):
    background = Image.open(absolute_path + "image_module/card_template.png")
    url = get_avatar(user=new_user)

    # download avatar
    avatar = Image.open(io.BytesIO(get_image(url=url)))
    
    # scaling
    base_width = 220
    w_percent = (base_width / float(avatar.size[0]))
    h_size = int((float(avatar.size[1]) * float(w_percent)))
    avatar = avatar.resize((base_width, h_size), Image.Resampling.LANCZOS)

    #load fonts
    if len(new_user.name) > 15:
        name_font = ImageFont.truetype(font=(absolute_path + "image_module/RUNES.ttf"), size=80)
    else:
        name_font = ImageFont.truetype(font=(absolute_path + "image_module/RUNES.ttf"), size=100)

    footer_font = ImageFont.truetype(font=(absolute_path + "image_module/MAGIC.ttf"), size=35)

    draw = ImageDraw.Draw(background)

    #write on background
    if len(new_user.name) > 9:
        draw.text(xy=(995, 115), text=new_user.name, fill=(235, 235, 235), font=name_font, align="center", anchor='rm')
    else:
        draw.text(xy=(795, 115), text=new_user.name, fill=(235, 235, 235), font=name_font, align="center", anchor='mm')
    
    draw.text(xy=(790, 200), text=f"We are now {all_members} members!", fill=(235, 235, 235), font=footer_font, align="center", anchor='mm')

    # add mask
    blur_radius = 1
    mask = Image.new(mode="L", size=avatar.size, color=0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(xy=(5, 8, base_width-5, base_width-5), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

    background.paste(im=avatar, box=(215, 20), mask=mask)
    
    # save
    bytes = io.BytesIO()
    background.save(bytes, format="PNG")
    bytes.seek(0)
    
    return File(bytes, filename="card.png")


def get_json_info(url):
    # create HTTP response object 
    response = requests.get(url)

    try:
        return json.loads(response.content)
    except:
        raise ValueError("NO JSON FILE FOUND!")


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
                    birthday_date[2] = int(birthday_date[2]) if (int(birthday_date[2]) != datetime.now().year) else 1900
                    birthday = datetime(day=int(birthday_date[0]), month=int(birthday_date[1]), year=int(birthday_date[2]))
                else:
                    birthday = None
            
            elif idx == "7":
                extra = field.value if (field.value != "-") else None
            
        return (user_id, game_id, from_wb, old_username, multiple_choice, additional_info, birthday, extra, 0,)
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

    line_2 = houses[[house for house in houses if house in roles][0]]
    embed.add_field(name="2. My house is...", value=line_2, inline=True)
    
    line_3 = (("Yes | " if portkey["from_wb"] else "No, ") + portkey["old_username"]) if portkey["old_username"] else ("Yes" if portkey["from_wb"] else "No")
    embed.add_field(name="3. Am I from the WB server? | My name was...", value=line_3.replace(" | 0", ", "), inline=False)

    line_4 = "• " + "• ".join([form_answers_extended[idx] for idx,choice in enumerate(portkey["multiple_choice"][::-1] + ("1" if portkey["additional_info"] else "0")) if choice == "1"])
    embed.add_field(name="4. In the game I like doing...", value=line_4, inline=False)
    
    if (not_skip := portkey["birthday"] is not None):
        line_5 = portkey["birthday"].strftime("%d.%m.%Y") if portkey["birthday"].year != 1900 else portkey["birthday"].strftime("%d.%m")
        embed.add_field(name="5. I was born...", value=line_5, inline=False)

    if portkey["extra"]:
        line_6 = portkey["extra"]
        embed.add_field(name=f"{6 if not_skip else 5}. You may also want to know...", value=line_6, inline=False)
    
    embed.set_footer(text=f"GOP  •  Portkey #{portkey['id']}")

    return embed


def print_house_members(members, page, filter):
    
    # filter by house and group
    house = list(houses.keys())[page]
    group = ["club", "guest", "cross guild"][filter]

    _ = "\n"

    users = []
    for member in members:
        roles = [role.name for role in member.roles]

        if house in roles and group in roles:
            users += [member]

    users = sorted(users, key=lambda x: (x.nick or x.global_name))
    
    i = 1
    for idx, user in enumerate(users):
        if user:
            users[idx] = f"{f'**{group.capitalize()}:**{_}' if (i == 1) else ''}{idx}. {user.nick or user.global_name} - <@{user.id}>"
            i += 1

    return Embed(color=system_embed_color, title=houses[house], description="\n".join(users))