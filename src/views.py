from src.functions import disable_after, print_house_members

from discord.enums import ButtonStyle
from discord.ext import commands
from discord.interactions import Interaction
from discord.partial_emoji import PartialEmoji
from discord.ui import button, Button, View, Select

from random import choice


# welcome message
class WelcomeView(View):
    
    def __init__(self, user, stickers):
        super().__init__(timeout=None)
        
        self.user = user
        self.stickers = stickers
        self.clicked_users = []
    
    # click button to send sticker
    @button(label="Raise your wand in greetings!",  style=ButtonStyle.grey, emoji=PartialEmoji.from_str("<:wandsup:1256318918943969391>"), custom_id="welcome")
    async def hello(self, interaction: Interaction, button: Button):
        
        if self.user is None:
            return await interaction.response.send_message("User not found!", ephemeral=True)
        
        elif interaction.user.id == self.user.id:
            return await interaction.response.send_message("You can't do it yourself, let others greet you!", ephemeral=True)

        if interaction.user.id not in self.clicked_users:
            self.clicked_users.append(interaction.user.id)

            sticker = choice(self.stickers)

            #NOTE if they ever allow webhooks to send stickers
            await interaction.response.send_message("Your message has been sent!", ephemeral=True)
            await interaction.message.reply(content=f"<@{interaction.user.id}> says: Welcome <@{self.user.id}>! {sticker.description}", stickers=[sticker])

        else:
            await interaction.response.send_message("We limited the interactions to one greeting per user!", ephemeral=True)


# disciplines in a dropdown select
class DisciplinesView(View):
    def __init__(self, options):
        super().__init__(timeout=None)

        self.dropdown = self.DisciplinesList(options, self)
        self.picked = None

        self.add_item(self.dropdown)
    
    @disable_after
    async def respond(self, interaction:Interaction, choice_idx):
        self.picked = choice_idx

    class DisciplinesList(Select):
        def __init__(self, options, parent_view):
            super().__init__(placeholder="Choose an option...", options=options)
            
            self.parent_view = parent_view

        async def callback(self, interaction:Interaction):
            selected_value = int(self.values[0])
            matching_index = next((i for i, option in enumerate(self.options) if option.value == selected_value), None)
            await self.parent_view.respond(interaction, choice_idx=matching_index)


# questions in a dropdown select
class QuestionnaireView(View):
    def __init__(self, options):
        super().__init__(timeout=None)
        
        self.dropdown = self.QuestionnaireList(options, self)
        self.picked   = None

        self.add_item(self.dropdown)
    
    @disable_after
    async def respond(self, interaction:Interaction, choice):
        self.picked = choice
    
    class QuestionnaireList(Select):
        def __init__(self, options, parent_view):
            super().__init__(placeholder="Choose an option...", options=options)
            
            self.parent_view = parent_view

        async def callback(self, interaction:Interaction):
            selected_value = self.values[0]
            await self.parent_view.respond(interaction, choice=True if selected_value == "True" else False if selected_value == "False" else int(selected_value) if selected_value.isdigit() else None)
    

# view members list
class MemberView(View):
    def __init__(self, members, message):
        super().__init__(timeout=None)
        
        self.members = members

        if message is not None:
            self.message = message
            self.cooldown = commands.CooldownMapping.from_cooldown(rate=1, per=5, type=commands.BucketType.member)
        else:
            self.message = None

        self.page = 0
        self.filter = 0
    
    # print a new list
    async def print_list(self, interaction=None):
        embed = print_house_members(self.members, self.page, self.filter)
        
        if self.message is not None:
            await self.message.edit(embed=embed, view=self)
        else:
            self.message = await interaction.response.send_message(embed=embed, view=self, ephemeral=True)
    
    # change printed members
    async def update_members(self, members):
        self.members = members
        await self.print_list()

    # cooldown between button presses
    def cooldown_interaction(func):
        async def response(self, interaction: Interaction, button: Button): 
            
            # handle cooldown for interactions if message exists
            if self.message is not None:
                bucket = self.cooldown.get_bucket(interaction.message)
                retry = bucket.update_rate_limit()

                if retry:
                    return await interaction.response.send_message(f"Slow down! Try again in {round(retry, 1)} seconds.", ephemeral=True)

            # call the actual button handler
            func(self, interaction, button)

             # after interaction, update the list
            await self.print_list(interaction)
            
            # defer the response if message exists
            if self.message is not None:
                return await interaction.response.defer()
    
        return response

    # turn pages/filters of list
    def turn_limit(self, turnable: int, max: int) -> int:
        return (turnable + max + 1) % (max + 1)

    @button(label="",  style=ButtonStyle.grey, emoji="⬅️", custom_id="left")
    @cooldown_interaction
    def turn_left(self, interaction: Interaction, button: Button):
        self.page = self.turn_limit(turnable=(self.page-1), max=3)

    @button(label="",  style=ButtonStyle.grey, emoji="➡️", custom_id="right")
    @cooldown_interaction
    def turn_right(self, interaction: Interaction, button: Button):
        self.page = self.turn_limit(turnable=(self.page+1), max=3)
    
    @button(label="GOP",  style=ButtonStyle.red, custom_id="filter")
    @cooldown_interaction
    def switch_filter(self, interaction: Interaction, button: Button):
        self.filter = self.turn_limit(turnable=(self.filter+1), max=2)

        if self.filter == 0:
            self.children[2].label = "GOP"
            self.children[2].style = ButtonStyle.red
        elif self.filter == 1:
            self.children[2].label = "Guest"
            self.children[2].style = ButtonStyle.green
        else:
            self.children[2].label = "Cross Guild"
            self.children[2].style = ButtonStyle.blurple