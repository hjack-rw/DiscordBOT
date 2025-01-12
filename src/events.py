from src.body import bot
from src.db_classes import WelcomeMessages
from src.functions import send_webhook, draw_infocard
from src.variables import test_bot, server_id, channel_ids, channel_ids_test, system_embed_color
from src.views import WelcomeView

from discord.embeds import Embed


# SETTINGS
# for testing
# test_bot["test_events"] = True # overwrite if needed

if test_bot["test_events"]:
    channel_ids = channel_ids_test


# Welcoming event
@bot.event
async def on_member_join(new_user):
    if not new_user.bot:
        server = bot.get_guild(server_id)
        channel = server.get_channel(channel_ids["welcome"])
        
        image = draw_infocard(new_user=new_user, all_members=len([member for member in server.members if not member.bot]))

        embed = Embed(title=f"Welcome, {new_user.name}, to GatesOfPurgatory! <:hugs:1256225688403447888>",  description="Go to <id:guide> and follow the instructions :)", color=system_embed_color)
        embed.set_image(url="attachment://card.png")
        embed.set_footer(text=f'''"You are a Wizard, {new_user.name}."''')
        
        message = await send_webhook(target_channel=channel, user_name="Prof. Hagrid", content=f"Mention: <@{new_user.id}>", embed=embed, file=image, view=WelcomeView(user=new_user, stickers=server.stickers))
        
        if not test_bot["test_events"]:
            WelcomeMessages().add(message.id)
    else:
        print(f"BOT: {new_user.name} joined the server!")