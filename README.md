# discord-mute-bot

Discord Mute Bot is a simple discord bot written in Python 3.8 that is designed to help muting an entire channel when
playing Among Us in a voice channel.

## Installation
- Install Python 3.8
- [Install the discord.py library](https://discordpy.readthedocs.io/en/latest/intro.html#installing) using pip
- Clone this repository
- Create a file named SECRETS.py and enter your discord bot token and discord-id, i.e.
<pre>
TOKEN=123456789ABCDEFG
OWNER_ID=987654321
</pre>
[How to get a token](https://discordpy.readthedocs.io/en/latest/discord.html#discord-intro)

- Run Bot.py
- optional: change prefix and activity of the bot at the top of Bot.py
- Create voice channels "Crew" and "Ghosts" on your discord
- Create role named "Mute Master" on your discord

## Features

### Commands
- **[prefix]mute:** Mutes everyone currently connected to your voic echat, requires a role named "Mute Master".
- **[prefix]unmute:** Unmutes everyone currently connected to your voice chat, requires a role named "Mute Master".
- **[prefix]disable:** Disables all functions of the bot, can only be run by bot-owner.
- **[prefix]enable:** Reenables all functions of the bot, can only be run by bot-owner.
- **[prefix]activity:** Changes the activity of the bot, can only be run by bot-owner.

### Other
- People who join the "Crew"-channel, while mute is active will automatically be muted.
- People joining the "Ghosts"-channel will be automatically unmuted.
- People who are muted and join the "Crew"-channel, while mute is inactive, will automatically be unmuted.
