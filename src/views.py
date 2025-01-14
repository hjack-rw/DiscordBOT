from src.tasks import housecup_disciplines_names

from discord.components import SelectOption
from discord.enums import ButtonStyle
from discord.interactions import Interaction
from discord.partial_emoji import PartialEmoji
from discord.ui import button, Button, View, Select

from random import choice


__all__ = ["WelcomeView", "DropdownView"] 


# welcome button
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


# dropdown select
class DropdownView(View):    
    def __init__(self, options):
        super().__init__(timeout=None)
        self.add_item(self.DropdownList(options))
        self.options = options
        self.picked = None
    
    async def respond(self, interaction:Interaction, choice):
        self.picked = int(choice)
        self.children[0].disabled= True
        await interaction.message.edit(view=self)
        await interaction.response.defer()
        self.stop()

    class DropdownList(Select):
        def __init__(self, options):
            # invert dictionary
            housecup_disciplines = {v:k for k,v in housecup_disciplines_names.items()}
            super().__init__(options=[SelectOption(label=option, value=housecup_disciplines[option]) for option in options])
        
        async def callback(self, interaction:Interaction):
            await self.view.respond(interaction, choice=self.values[0])