import os
import sys

os.environ['LIVE_BOT_TWITCH_SEARCH'] = "" # Client ID from twitch (searching people via add command)
os.environ['LIVE_BOT_TWITCH_UPDATE'] = "" # Client ID from twitch (updating user information for notifications)
os.environ['LIVE_BOT_TWITCH_LIVE'] = "" # Client ID from twitch (checking if people are live)
os.environ['LIVE_BOT_CLIENT_ID'] = "" # The Client ID from Discord
os.environ['LIVE_BOT_TOKEN'] = "" # The Token from Discord
os.environ['LIVE_BOT_DEBUG_MODE'] = "" # Is Django in Debug mode?
os.environ['LIVE_BOT_ALERT_CHANNEL'] = "" # Alert channel ID
os.environ['LIVE_BOT_OWNER_ID'] = "131224383640436736" # Replace with your own Discord ID
os.environ['LIVE_BOT_DJANGO_SECRET'] = "1234567890" # Django secret for the database
os.environ['LIVE_BOT_DATABASE_ENGINE'] = "" # What should the database be?
os.environ['LIVE_BOT_DATABASE_NAME'] = "" # Django database name
os.environ['LIVE_BOT_DATABASE_HOST'] = "" # Django database host
os.environ['LIVE_BOT_DATABASE_USERNAME'] = "" # Django database username
os.environ['LIVE_BOT_DATABASE_PASSWORD'] = "" # Django database password
os.environ['LIVE_BOT_DATABASE_PORT'] = "" # Django database port
os.environ['LIVE_BOT_EMAIL_PASSWORD'] = "" # Django email password
os.environ['LIVE_BOT_DBOTS_KEY'] = "" # bots.discord.pw key
os.environ['LIVE_BOT_DBL_KEY'] = "" # discordbots.org key
