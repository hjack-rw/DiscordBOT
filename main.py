from src import bot, bot_token

if __name__ == '__main__':
    bot.run(bot_token)


#TODO! leaderboard:
# - make the db record: id, xp and custom_username, offset (?)
# / problem_name = {1108425644032938044:"Voodoochild", 776678540166823936:"LEIL", 1132281522041401454:"BADGER", 871307021138399232:"Tam Lin", 1140274502882820116: "S i r i u s"}
# / remove offset = {?:Polina, ?:Zalia, 1132281522041401454:Badger, 1108425644032938044:Voodoo, ?:Jlyata, ?:Draconi, ?:Eslamo, 1140274502882820116:Sirius, ?:Alki, }
# - (add / subtract / set) amount only > 0
# - while giving points post to channel
# - send the level up massege on both command and auto

#TODO! rework the sorthing-hat channel:
# ~house picking system and change nickname~
# ~add the member list permanent~
# - subscription system (see bellow:)

#TODO! subscription system:
# pick a subscription and add the role to members before the event
# clear all subscriptions on another button
# IMPORTANT: check if clearing the role keeps the notification!

#TODO! portkey:
# automatic add to a paste service

#TODO! sprout:
# trigger on herbology related stuff:
# weekly plants,
# own timers for plants with notification for the server:

# - for own timers use create_a_task that is run on restart of the bot:
# create_a_task(timer={"hours":0, "minutes":0, "seconds":0}).start(event_info={"id": 1})

# - the times are from the database. while creating save to database. after executing delete
# - limit for user that is set in code (2 for testing)
# - seperate into aquatic and non aquatic

#TODO! a queue for all events this day so if the bot restarts he knows if he has to send something
# - when they trigger normally just remove them