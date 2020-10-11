import discord
import SECRETS

game = discord.Game("ur sus")
client = discord.Client(activity=game)


@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(">info"):
        output = ""
        if message.author.voice and message.author.voice.channel:
            channel = message.author.voice.channel
            output += "{0} is connected to channel {1} (id: {2})\n".format(str(message.author), str(channel),
                                                                           str(channel.id))
            voice_members = channel.members
            output += "Connected are:"
            for member in voice_members:
                output += "\n" + str(member)
        await message.channel.send(output)
        print(output)

    elif message.content.startswith(">mute"):
        if message.author.voice and message.author.voice.channel:
            channel = message.author.voice.channel
            for member in channel.members:
                await member.edit(mute=True)

    elif message.content.startswith(">unmute"):
        if message.author.voice and message.author.voice.channel:
            channel = message.author.voice.channel
            for member in channel.members:
                await member.edit(mute=False)


client.run(SECRETS.TOKEN)
