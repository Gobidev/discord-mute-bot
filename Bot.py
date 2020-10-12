import discord
from discord.ext import commands
import time
import asyncio
import SECRETS


MUTE_GUILD = {}
DISABLED = False


def print_log(*args, **kwargs):
    t = time.strftime("%Y-%m-%d %T")
    print(t, *args, **kwargs)
    with open('Bot.log', 'a') as file:
        print(t, *args, **kwargs, file=file)


bot = commands.Bot(command_prefix=">", activity=discord.Game("WORK IN PROGRESS"))


@bot.event
async def on_ready():
    global MUTE_GUILD
    print_log('Logged in as {0.user}'.format(bot))
    for guild in bot.guilds:
        MUTE_GUILD[guild.id] = False
    print_log("Guilds:", MUTE_GUILD)


@bot.event
async def on_guild_join(guild):
    global MUTE_GUILD
    MUTE_GUILD[guild.id] = False


@bot.event
async def on_voice_state_update(member, before, after):
    if DISABLED:
        return

    if before.channel is not None:
        guild = before.channel.guild
    else:
        guild = after.channel.guild

    mute_server = MUTE_GUILD[guild.id]

    if before.channel is not after.channel:
        print_log("Voice state update: {0} from {1} to {2} on Guild {3}".format(
            member, before.channel, after.channel, guild))

    if after is not None and before.channel is not after.channel:
        if str(after.channel) == "Tote":
            await member.edit(mute=False)
        elif str(after.channel) == "Crew":
            if mute_server:
                await member.edit(mute=True)
            else:
                await member.edit(mute=False)


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == 480284798028611584
    return commands.check(predicate)


async def handle_command(ctx):
    await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
    await asyncio.sleep(3)
    await ctx.message.delete()


@bot.command()
async def info(ctx):
    if DISABLED:
        return
    output = ""
    if ctx.message.author.voice and ctx.message.author.voice.channel:
        channel = ctx.message.author.voice.channel
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
        output += "{0} is connected to channel {1} (id: {2})\n".format(str(ctx.message.author), str(channel),
                                                                       str(channel.id))
        voice_members = channel.members
        output += "Connected are:"
        for member in voice_members:
            output += "\n" + str(member)
    await ctx.send(output)
    print_log(output)


@bot.command()
@commands.has_role("Mute Master")
async def mute(ctx):
    if DISABLED:
        return
    global MUTE_GUILD
    if ctx.message.author.voice and ctx.message.author.voice.channel:
        print_log("Triggered mute in Guild", ctx.guild)
        channel = ctx.message.author.voice.channel
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
        for member in channel.members:
            await member.edit(mute=True)
            MUTE_GUILD[ctx.guild.id] = True


@bot.command()
@commands.has_role("Mute Master")
async def unmute(ctx):
    if DISABLED:
        return
    global MUTE_GUILD
    if ctx.message.author.voice and ctx.message.author.voice.channel:
        print_log("Triggered unmute in Guild", ctx.guild)
        channel = ctx.message.author.voice.channel
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
        for member in channel.members:
            await member.edit(mute=False)
            MUTE_GUILD[ctx.guild.id] = False


@bot.command()
@is_owner()
async def disable(ctx):
    global DISABLED
    DISABLED = True
    print_log("Bot is now disabled")
    await handle_command(ctx)


@bot.command()
@is_owner()
async def enable(ctx):
    global DISABLED
    DISABLED = False
    print_log("Bot is now enabled")
    await handle_command(ctx)


bot.run(SECRETS.TOKEN)
