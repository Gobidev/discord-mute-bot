import discord
from discord.ext import commands
import time
import asyncio
import psutil
import SECRETS

PREFIX = "."
ACTIVITY = discord.Game("I mute U")
OWNER_ID = SECRETS.OWNER_ID
TOKEN = SECRETS.TOKEN
GAME_CHANNEL_NAME = "Crew"
DEAD_CHANNEL_NAME = "Ghosts"
MUTE_PERMISSION_ROLE_NAME = "Mute Master"

# ------------------- DO NOT CHANGE THESE -------------------
MUTE_GUILD = {}
DISABLED = False
bot = commands.Bot(command_prefix=PREFIX, activity=ACTIVITY)


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
    print_log("{1}: '{0}' (in channel {2} on guild {3})".format(message.content, message.author, message.channel,
                                                                message.channel.guild))
    if message.author == bot.user:
        if message.content != "":
            await asyncio.sleep(4)
            await message.delete()
    else:
        await bot.process_commands(message)


@bot.event
async def on_guild_join(guild):
    global MUTE_GUILD
    MUTE_GUILD[guild.id] = False


@bot.event
async def on_command_error(ctx, error):
    print_log(error)
    if isinstance(error, commands.errors.CommandNotFound):
        await react(ctx, False)
        await ctx.send("Invalid command.")
        await delete_message(ctx)


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
        if str(after.channel) == DEAD_CHANNEL_NAME:
            await member.edit(mute=False)
            print_log("Un-muted member", member, "in channel", after.channel, "on guild", after.channel.guild)
        elif str(after.channel) == GAME_CHANNEL_NAME:
            if mute_server:
                await member.edit(mute=True)
                print_log("Muted member", member, "in channel", after.channel, "on guild", after.channel.guild)
            else:
                await member.edit(mute=False)
                print_log("Un-muted member", member, "in channel", after.channel, "on guild", after.channel.guild)


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
    await asyncio.sleep(2)
    await ctx.message.delete()


# ------------------- COMMANDS -------------------
@bot.command(aliases=["ping", "info", "p"])
async def status(ctx):
    await react(ctx)
    embed = discord.Embed(title="Bot Status", color=discord.Color.orange())
    embed.add_field(name="Status", value=":red_circle: Disabled" if DISABLED else ":green_circle: Enabled")
    embed.add_field(name="Ping", value=":clock1: " + str(round(bot.latency * 1000)) + "ms")
    embed.add_field(name="CPU", value=":desktop: " + str(psutil.cpu_percent()) + "%")
    embed.add_field(name="RAM", value=":film_frames: " + str(round(psutil.virtual_memory().used * 10 ** -9, 2)) +
                                      "GB/" + str(round(psutil.virtual_memory().total * 10 ** -9, 2)) + "GB")
    embed.add_field(name="Guilds", value=":house: " + str(len(bot.guilds)))
    amount_users = 0
    for guild in bot.guilds:
        for _ in guild.members:
            amount_users += 1
    embed.add_field(name="Users", value=":people_holding_hands: " + str(amount_users))
    creator = bot.get_user(480284798028611584)
    embed.set_footer(text="made by {0}".format(creator), icon_url=creator.avatar_url)
    await ctx.send(embed=embed)
    await delete_message(ctx)


@bot.command(aliases=["m"])
@commands.has_role(MUTE_PERMISSION_ROLE_NAME)
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
    else:
        await react(ctx, False)
        await ctx.send("You need to be connected to a voice chat to use this command.")
        await delete_message(ctx)


@bot.command(aliases=["um", "u"])
@commands.has_role(MUTE_PERMISSION_ROLE_NAME)
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
    else:
        await react(ctx, False)
        await ctx.send("You need to be connected to a voice chat to use this command.")
        await delete_message(ctx)


# ------------------- OWNER COMMANDS -------------------
@bot.command()
@is_owner()
async def activity(ctx, *args):
    global ACTIVITY
    if DISABLED:
        await react(ctx, False)
        await ctx.send("Bot is disabled.")
        await delete_message(ctx)
        return
    if len(args) < 1:
        await react(ctx, False)
        await ctx.send("Invalid usage: {0}activity 'New Activity'".format(PREFIX))
        await delete_message(ctx)
        return
    await react(ctx)
    new_activity = ""
    for n in args:
        new_activity += n + " "
    ACTIVITY = discord.Game(new_activity)
    await bot.change_presence(activity=ACTIVITY)
    print_log("Changed activity to '{0}'".format(new_activity))
    await delete_message(ctx)


@bot.command()
@is_owner()
async def disable(ctx):
    global DISABLED
    if DISABLED:
        await react(ctx, False)
        await ctx.send("The Bot is already disabled.")
        await delete_message(ctx)
        return
    await react(ctx)
    DISABLED = True
    print_log("Bot is now disabled")
    await bot.change_presence(activity=discord.Game("disabled \N{NO ENTRY}"))
    await delete_message(ctx)


@bot.command()
@is_owner()
async def enable(ctx):
    global DISABLED
    if not DISABLED:
        await react(ctx, False)
        await ctx.send("The Bot is already enabled.")
        await delete_message(ctx)
        return
    await react(ctx)
    DISABLED = False
    print_log("Bot is now enabled")
    await bot.change_presence(activity=ACTIVITY)
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
    if isinstance(error, commands.errors.CheckFailure):
        await react(ctx, False)
        await ctx.send("You don't have permissions to do that.")
        print_log("No ownership error of User", ctx.message.author, "in Guild", ctx.guild)
        await delete_message(ctx)


bot.run(TOKEN)
