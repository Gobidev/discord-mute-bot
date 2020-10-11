import discord
from discord.ext import commands
import SECRETS

bot = commands.Bot(command_prefix=">", activity=discord.Game("ur sus"))


MUTE = False


@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is not after.channel:
        print("Voice state update: {0} from {1} to {2}".format(member, before.channel, after.channel))
    if after is not None and before.channel is not after.channel:
        if str(after.channel) == "Tote":
            await member.edit(mute=False)
        elif str(after.channel) == "Crew":
            if MUTE:
                await member.edit(mute=True)
            else:
                await member.edit(mute=False)



@bot.command()
async def info(ctx):
    output = ""
    if ctx.message.author.voice and ctx.message.author.voice.channel:
        channel = ctx.message.author.voice.channel
        output += "{0} is connected to channel {1} (id: {2})\n".format(str(ctx.message.author), str(channel),
                                                                       str(channel.id))
        voice_members = channel.members
        output += "Connected are:"
        for member in voice_members:
            output += "\n" + str(member)
    await ctx.send(output)
    print(output)


@bot.command()
@commands.has_role("Mute Master")
async def mute(ctx):
    global MUTE
    if ctx.message.author.voice and ctx.message.author.voice.channel:
        channel = ctx.message.author.voice.channel
        for member in channel.members:
            await member.edit(mute=True)
            MUTE = True


@bot.command()
@commands.has_role("Mute Master")
async def unmute(ctx):
    global MUTE
    if ctx.message.author.voice and ctx.message.author.voice.channel:
        channel = ctx.message.author.voice.channel
        for member in channel.members:
            await member.edit(mute=False)
            MUTE = False


bot.run(SECRETS.TOKEN)
