# discord-mute-bot

Discord Mute Bot is a simple discord bot written in Python 3.8 that is designed to help muting an entire channel when
playing Among Us in a voice channel.

## Installation
- Install Python 3.8
- [Install the discord.py library](https://discordpy.readthedocs.io/en/latest/intro.html#installing) and the psutil
library using pip
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

### The basic commands are:
- **.[mute|m]** to mute all members currently connected to your voice chat.
- **.[unmute|um|u]** to unmute all members currently connected to your voice chat.
- **.[status|ping|info|p]** to get current information about the bot.
- **.[help] (command)** for help.
- **.[config|cfg|settings]** (Admins only) to change bot configuration for the guild. Settings include changing the role to mute, the channel names of the game and ghosts channel and wether server mute is suppressed or not.
- **.[invite|i|inv]** to get the invite code to add this bot to a guild.
- **.[code|c|game|host] (skeld|mira|polus) (eu|na|asia)** to show a game code in a nice embed. You can use .config code-channel to only allow a certain channel for codes to be sent.


### It also does the following in the background:
- People who join the voice chat while the game is running will automatically be muted.
- People who move to a "dead" channel will automatically be unmuted and muted again if they rejoin the game channel.
- People who are muted and join the game channel while mute is not active will be automatically unmuted.
- Other server mute actions performed by guild members will be suppressed. This is disabled per default, you can enable it with .config toggle