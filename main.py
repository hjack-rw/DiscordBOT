from src import bot, bot_token

if __name__ == '__main__':
    bot.run(bot_token)


#TODO! list all members of a house
# each house a page. buttons to turn pages (?)

#TODO! subscription system:
# pick a subscription / clear all subscriptions on button. add the role to members before the event
# IMPORTANT: check if clearing the role keeps the notification!

#TODO! portkey:
#automatic add to a paste service

#TODO! create own custom cards for leaderboard:
# chocolate frog theme, with house colors

#TODO! sprout:
# trigger on herbology related stuff:
# weekly plants,
# own timers for plants with notification for the server:

# - for own timers use create_a_task that is run on restart of the bot:
# create_a_task(timer={"hours":0, "minutes":0, "seconds":0}).start(event_info={"id": 1})

# - the times are from the database. while creating save to database. after executing delete
# - limit for user that is set in code (2 for testing)
# - seperate into aquatic and non aquatic