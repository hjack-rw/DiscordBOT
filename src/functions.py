from src.variables import server_id, webhook_id, wait_for, absolute_path, discord_token, bot_token

from discord.file import File
from discord.utils import MISSING

from PIL import Image, ImageFont, ImageDraw, ImageFilter

import requests
session = requests.Session()

import io
import json
import time

__all__ = ["send_command", "send_message", "send_webhook", "get_avatar", "draw_infocard"] 


headers = {"authorization": f"Bot {bot_token}",
            "content-type": "application/json",
            "user-agent": "BOT (http://discord.com, v1.0)",}



def send_command(target_channel_id, app_id, version, id, command, options=[]):
    payload = {"type":2,
               "application_id":app_id,
               "guild_id":server_id,
               "channel_id":target_channel_id,
               "session_id":"98f3ba46da80ad7b5c2735ecb19af45d",
               "data":{"version":version, "id":id, "name":command, "options": options}}
    
    # overwrite headers
    headers = {"authorization": discord_token,
               "content-type": "application/json",}

    response = session.post(url="https://discord.com/api/v9/interactions", json=payload, headers=headers)
    print(response)

    if response.status_code < 300:
        time.sleep(wait_for)
    else:
        raise ValueError("FAILED TO SEND COMMAND!")



def send_message(target_channel_id, content, message_id=None, stickers=[]):
    payload = {"content":content, "sticker_ids":stickers}
    
    if message_id:
        payload.update({"message_reference": {"channel_id": target_channel_id, "message_id": message_id}})
    
    print(session.post(url=f"https://discord.com/api/v9/channels/{target_channel_id}/messages", data=json.dumps(payload), headers=headers))
    time.sleep(wait_for)



async def send_webhook(target_channel, user_name, user_avatar_url=None, content="", embed=None, file=None, view=None):            
    payload = {"channel_id":target_channel.id}
    
    if user_avatar_url is None:
        custom_avatars = {"Prof. Dumbledore": "https://static.wikia.nocookie.net/harrypotter/images/8/82/ProfessorDumbledore.jpg",
                          "Prof. McGonagall": "https://m.natemat.pl/4cccf528bb2fabc88d662c3ac8a519ef,922,0,0,0.png",
                          "Prof. Hagrid": "https://ostatniatawerna.pl/wp-content/cache/thumb/7c/f366d57c85cd27c_730x452.jpg",}
    
        try:
            user_avatar_url = custom_avatars[user_name]
        except KeyError:
            user_avatar_url = custom_avatars["Prof. Dumbledore"]
    
    response = session.patch(f"https://discordapp.com/api/webhooks/{webhook_id}", json=payload, headers=headers)
    print(response)

    if response.status_code == 200:
        webhook = [webhook for webhook in await target_channel.webhooks() if webhook.id == webhook_id][0]
        
        embed = embed if embed else MISSING
        file = file if file else MISSING
        view = view if view else MISSING

        return await webhook.send(content=content, username=user_name, avatar_url=user_avatar_url, embed=embed, file=file, view=view, wait=True)
    else:
        raise ValueError("FAILED TO CREATE WEBHOOK!")


def get_avatar(user):
    try:
        return user.avatar._url
    except AttributeError:
        return user.default_avatar._url

def draw_infocard(new_user, all_members):
    background = Image.open(absolute_path + "image_module/card_template.png")

    # download avatar
    response = session.get(get_avatar(new_user))
    avatar = Image.open(io.BytesIO(response.content))
    

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