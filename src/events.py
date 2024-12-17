from pre_init import test_events

from src.body import bot
from src.db_classes import WelcomeMessages
from src.functions import send_webhook, draw_infocard
from src.variables import local_deploy, server_id, channel_ids, channel_ids_test, system_embed_color
from src.views import WelcomeView

from discord.embeds import Embed


# SETTINGS
if local_deploy:
    test_events = True # overwrite if needed


# for testing
if test_events:
    channel_ids = channel_ids_test


# Welcoming event
@bot.event
async def on_member_join(new_user):
    print("Recognised that a member called " + new_user.name + "," + f"{new_user.id}" + " joined")

    server = bot.get_guild(server_id)
    channel = server.get_channel(channel_ids["welcome"])
    
    image = draw_infocard(new_user=new_user, all_members=len([member for member in server.members if not member.bot]))

    embed = Embed(title=f"Welcome, {new_user.name}, to GatesOfPurgatory! <:hugs:1256225688403447888>",  description="Go to <id:guide> and follow the instructions :)", color=system_embed_color)
    embed.set_image(url="attachment://card.png")    
    
    message = await send_webhook(target_channel=channel, user_name="Prof. Hagrid", content=f"Mention: <@{new_user.id}>", embed=embed, file=image, view=WelcomeView(user=new_user, stickers=server.stickers))
    WelcomeMessages().add_message_id(message.id)