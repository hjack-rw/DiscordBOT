from src.variables import channel_ids, channel_ids_test, local_deploy

from discord.enums import ButtonStyle
from discord.interactions import Interaction
from discord.partial_emoji import PartialEmoji
from discord.ui import button, Button, View

from random import choice


__all__ = ["WelcomeView"] 


# SETTINGS 
test_views = True if local_deploy else False
#// test_views = True # an overwrite


# for testing
if test_views:
    channel_ids = channel_ids_test



# welcome view
class WelcomeView(View):
    
    def __init__(self, user, stickers):
        super().__init__(timeout=None)
        self.user = user
        self.stickers = stickers
        self.clicked_users = []
    
    # welcome button
    @button(label="Raise your wand in greetings!",  style=ButtonStyle.grey, emoji=PartialEmoji.from_str("<:wandsup:1256318918943969391>"), custom_id="welcome")
    async def hello(self, interaction: Interaction, button: Button):
        
        if self.user is None:
            print(self.user)
            return await interaction.response.send_message("User not found!", ephemeral=True)
        
        elif interaction.user.id == self.user.id:
            return await interaction.response.send_message("You can't do it yourself, let others greet you!", ephemeral=True)

        else:
            if interaction.user.id not in self.clicked_users:
                self.clicked_users += [interaction.user.id]

                sticker = choice(self.stickers)

                # TODO! If they ever allow webhooks to send stickers
                await interaction.response.send_message("Your message has been sent!", ephemeral=True)
                await interaction.message.reply(content=f"<@{interaction.user.id}> says: Welcome <@{self.user.id}>! {sticker.description}", stickers=[sticker])

            else:
                await interaction.response.send_message("We limited the interactions to one greeting per user!", ephemeral=True)