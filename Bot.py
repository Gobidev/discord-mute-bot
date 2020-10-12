import discord
from discord.ext import commands
import time
import asyncio
import SECRETS


MUTE_GUILD = {}
DISABLED = False

PREFIX = ">"
OWNER_ID = SECRETS.OWNER_ID
TOKEN = SECRETS.TOKEN
DEFAULT_ACTIVITY = discord.Game("WORK IN PROGRESS")
bot = commands.Bot(command_prefix=PREFIX, activity=DEFAULT_ACTIVITY)


# ------------------- EVENTS -------------------
@bot.event
async def on_ready():
    global MUTE_GUILD
    print_log('Logged in as {0.user}'.format(bot))
    for guild in bot.guilds:
        MUTE_GUILD[guild.id] = False
    print_log("Guilds:", MUTE_GUILD)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        await asyncio.sleep(5)
        await message.delete()
    else:
        await bot.process_commands(message)


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
        if str(after.channel) == "Ghosts":
            await member.edit(mute=False)
        elif str(after.channel) == "Crew":
            if mute_server:
                await member.edit(mute=True)
            else:
                await member.edit(mute=False)


# ------------------- OTHER FUNCTIONS -------------------
def print_log(*args, **kwargs):
    t = time.strftime("%Y-%m-%d %T")
    print(t, *args, **kwargs)
    with open('Bot.log', 'a') as file:
        print(t, *args, **kwargs, file=file)


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)


async def react(ctx, accepted=True):
    if accepted:
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
    else:
        await ctx.message.add_reaction("\N{NO ENTRY}")


async def delete_message(ctx):
    await asyncio.sleep(3)
    await ctx.message.delete()


# ------------------- COMMANDS -------------------
@bot.command()
async def info(ctx):
    if DISABLED:
        await react(ctx, False)
        await ctx.send("Bot is disabled.")
        await delete_message(ctx)
        return
    output = ""
    if ctx.message.author.voice and ctx.message.author.voice.channel:
        channel = ctx.message.author.voice.channel
        await react(ctx)
        output += "{0} is connected to channel {1} (id: {2})\n".format(str(ctx.message.author), str(channel),
                                                                       str(channel.id))
        voice_members = channel.members
        output += "Connected are:"
        for member in voice_members:
            output += "\n" + str(member)
    await ctx.send(output)
    print_log(output)
    await delete_message(ctx)


@bot.command()
@commands.has_role("Mute Master")
async def mute(ctx):
    if DISABLED:
        await react(ctx, False)
        await ctx.send("Bot is disabled.")
        await delete_message(ctx)
        return
    global MUTE_GUILD
    if ctx.message.author.voice and ctx.message.author.voice.channel:
        print_log("Triggered mute in Guild", ctx.guild)
        channel = ctx.message.author.voice.channel
        await react(ctx)
        for member in channel.members:
            await member.edit(mute=True)
            MUTE_GUILD[ctx.guild.id] = True
        print_log("Muted", str(len(channel.members)), "Members")
        await delete_message(ctx)


@bot.command()
@commands.has_role("Mute Master")
async def unmute(ctx):
    if DISABLED:
        await react(ctx, False)
        await ctx.send("Bot is disabled.")
        await delete_message(ctx)
        return
    global MUTE_GUILD
    if ctx.message.author.voice and ctx.message.author.voice.channel:
        print_log("Triggered unmute in Guild", ctx.guild)
        channel = ctx.message.author.voice.channel
        await react(ctx)
        for member in channel.members:
            await member.edit(mute=False)
            MUTE_GUILD[ctx.guild.id] = False
        print_log("Un-muted", str(len(channel.members)), "Members")
        await delete_message(ctx)


# ------------------- OWNER COMMANDS -------------------
@bot.command()
@is_owner()
async def activity(ctx, *args):
    if DISABLED:
        await react(ctx, False)
        await ctx.send("Bot is disabled.")
        await delete_message(ctx)
        return
    if len(args) < 1:
        await react(ctx, False)
        await ctx.send("Invalid usage: [prefix]activity 'New Activity'")
        await delete_message(ctx)
        return
    await react(ctx)
    new_activity = ""
    for n in args:
        new_activity += n + " "
    await bot.change_presence(activity=discord.Game(new_activity))
    print_log("Changed activity to '{0}'".format(new_activity))
    await delete_message(ctx)


@bot.command()
@is_owner()
async def disable(ctx):
    global DISABLED
    await react(ctx)
    DISABLED = True
    print_log("Bot is now disabled")
    await bot.change_presence(activity=discord.Game("disabled \N{NO ENTRY}"))
    await delete_message(ctx)


@bot.command()
@is_owner()
async def enable(ctx):
    global DISABLED
    await react(ctx)
    DISABLED = False
    print_log("Bot is now enabled")
    await bot.change_presence(activity=DEFAULT_ACTIVITY)
    await delete_message(ctx)


# ------------------- ERROR HANDLING -------------------
@mute.error
@unmute.error
async def mute_error(ctx, error):
    await react(ctx, False)
    await ctx.send(error)
    print_log("Mute Role error of User", ctx.message.author, "in Guild", ctx.guild)
    await delete_message(ctx)


@disable.error
@enable.error
@activity.error
async def no_ownership_error(ctx, error):
    await react(ctx, False)
    await ctx.send("You don't have permissions to do that.")
    print_log("No ownership error of User", ctx.message.author, "in Guild", ctx.guild)
    await delete_message(ctx)


bot.run(TOKEN)
