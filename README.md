## Live Bot
[![Build Status](https://travis-ci.org/bsquidwrd/Live-Bot.svg?branch=master)](https://travis-ci.org/bsquidwrd/Live-Bot) [![Documentation Status](https://readthedocs.org/projects/live-bot/badge/?version=latest)](http://live-bot.readthedocs.io/en/latest/?badge=latest) [![Coverage Status](https://coveralls.io/repos/github/bsquidwrd/Live-Bot/badge.svg?branch=master)](https://coveralls.io/github/bsquidwrd/Live-Bot?branch=master) [![Requirements Status](https://requires.io/github/bsquidwrd/Live-Bot/requirements.svg?branch=master)](https://requires.io/github/bsquidwrd/Live-Bot/requirements/?branch=master)


## Running
_NOTE: If you want to run this yourself, make sure the bot is a "Bot User"_

I'd prefer if only my instance was running so the bot and users don't get confused. You should only need one main configuration file while the rest will be created automatically. In the `web` directory, rename [environment_example.py](web/environment_example.py) to `environment.py`

[Click here to have the bot added to your server](https://discordapp.com/oauth2/authorize?client_id=225463490813493248&scope=bot&permissions=257104)

#### Environmental Variables
- `LIVE_BOT_BASE_DIR:` The directory all the files are located
- `LIVE_BOT_CLIENT_ID:` The Client ID assigned by Discord
- `LIVE_BOT_TOKEN:` The token used by Discord to sign in with your bot
- `LIVE_BOT_OWNER_ID:` The Discord ID for the owner of the bot


## Requirements
- Python 3.5+
- Async version of discord.py

## Thanks
- [Rapptz](https://github.com/Rapptz) and his amazing work on [Discord.py](https://github.com/Rapptz/discord.py) combined with the code I used as a template [RoboDanny](https://github.com/Rapptz/RoboDanny)
