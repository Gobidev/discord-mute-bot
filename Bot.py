import discord
from discord.ext import commands
import time
import asyncio
import pickle
import os.path
import psutil
import SECRETS

PREFIX = "."
OWNER_ID = SECRETS.OWNER_ID
TOKEN = SECRETS.TOKEN
LOG_CHAT = True


# ------------------- DO NOT EDIT THIS -------------------
def print_log(*args, **kwargs):
    t = time.strftime("%Y-%m-%d %T")
    print(t, *args, **kwargs)
    with open('Bot.log', 'a') as file:
        try:
            print(t, *args, **kwargs, file=file)
        except UnicodeEncodeError:
            print_log("Error writing log entry")


def load_guilds():
    global guilds
    if os.path.isfile("guilds.config"):
        with open("guilds.config", "rb") as config_file:
            guilds = pickle.load(config_file)
        print_log("Loaded {0} guild-configs from file".format(len(guilds)))


def save_guilds():
    global guilds
    with open("guilds.config", "wb") as config_file:
        pickle.dump(guilds, config_file)
    print_log("Saved config of {0} guilds to file".format(len(guilds)))


def get_guild_config(guild_id):
    global guilds
    for guild in guilds:
        if guild.guild_id == guild_id:
            return guild


class Guild:
    def __init__(self, guild):
        self.name = str(guild)
        self.guild_id = guild.id
        self.is_muted = False
        self.game_channel_name = "Crew"
        self.dead_channel_name = "Ghosts"
        self.mute_permissions_role = "Mute Master"
        self.block_server_mute = False

        print_log("Added guild", self.name)


DISABLED = False
ACTIVITY = None
guilds = []
load_guilds()

bot = commands.Bot(command_prefix=PREFIX)


# ------------------- EVENTS -------------------
@bot.event
async def on_ready():
    global guilds, ACTIVITY
    print_log('Logged in as {0.user}'.format(bot))

    if not guilds:
        for guild in bot.guilds:
            guilds.append(Guild(guild))
        print_log("Added {0} guilds to config".format(len(bot.guilds)))
        save_guilds()

    elif len(guilds) != len(bot.guilds):
        saved_guild_ids = []

        for guild in guilds:
            saved_guild_ids.append(guild.guild_id)
        new_guilds = 0

        for guild in bot.guilds:
            if guild.id not in saved_guild_ids:
                guilds.append(Guild(guild))
                new_guilds += 1

        print_log("Added {0} guilds to config".format(new_guilds))
        save_guilds()

    unmute_all_guilds()
    await update_default_activity()


@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.TextChannel):
        if LOG_CHAT:
            print_log("{1}: '{0}' (in channel {2} on guild {3})".format(message.content, message.author,
                                                                        message.channel, message.channel.guild))
    if message.author == bot.user:
        if message.content != "" and not message.content.startswith("```"):
            await asyncio.sleep(5)
            await message.delete()

    else:
        await bot.process_commands(message)


@bot.event
async def on_guild_join(guild):
    global guilds
    print_log("Joined guild", guild)
    guilds.append(Guild(guild))
    print("Added config for guild", guild)
    save_guilds()

    await update_default_activity()

"""
@bot.event
async def on_command_error(ctx, error):
    print_log(error)
    if isinstance(error, commands.errors.CommandNotFound):
        await react(ctx, False)
        await ctx.send("Invalid command.")
        await delete_message(ctx)
"""


@bot.event
async def on_voice_state_update(member, before, after):
    if DISABLED:
        return

    guild = get_guild_config(after.channel.guild.id)

    if before.channel is not after.channel:
        print_log("Voice channel change: {0} from {1} to {2} on Guild {3}".format(
            member, before.channel, after.channel, guild.name))
    else:
        if not guild.block_server_mute:
            return

    if after is not None:
        if str(after.channel) == guild.dead_channel_name and member.voice.mute:
            await member.edit(mute=False)
            print_log("Un-muted member", member, "in channel", after.channel, "on guild", guild.name)
        elif str(after.channel) == guild.game_channel_name:
            if guild.is_muted and not member.voice.mute:
                await member.edit(mute=True)
                print_log("Muted member", member, "in channel", after.channel, "on guild", guild.name)
            elif not guild.is_muted and member.voice.mute:
                await member.edit(mute=False)
                print_log("Un-muted member", member, "in channel", after.channel, "on guild", guild.name)


# ------------------- OTHER FUNCTIONS -------------------
def is_owner():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID

    return commands.check(predicate)


def has_mute_role():
    async def predicate(ctx):

        try:
            ctx.guild.id
        except AttributeError:
            return

        guild = get_guild_config(ctx.guild.id)
        author_roles = ctx.message.author.roles

        author_role_names = []
        for author_role in author_roles:
            author_role_names.append(author_role.name)

        if guild.mute_permissions_role not in author_role_names:
            return False
        else:
            return True

    return commands.check(predicate)


def unmute_all_guilds():
    global guilds
    for guild in guilds:
        guild.is_muted = False
    print_log("Un-muted all guilds")
    save_guilds()


async def react(ctx, accepted=True):
    if accepted:
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
    else:
        await ctx.message.add_reaction("\N{NO ENTRY}")


async def delete_message(ctx):
    if isinstance(ctx.channel, discord.TextChannel):
        await asyncio.sleep(2)
        await ctx.message.delete()


async def update_default_activity():
    global ACTIVITY
    ACTIVITY = "muting on {0} guilds".format(len(bot.guilds))
    await bot.change_presence(activity=discord.Game(ACTIVITY))


# ------------------- COMMANDS -------------------
@bot.command(aliases=["ping", "info", "p"], brief="Shows the current status of the bot",
             description="Shows if the bot is active, current ping time, CPU and RAM usage, number of guilds and the"
                         "number of users the bot has.")
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


@bot.command(aliases=["m"], brief="Mutes all members in a voice chat",
             description="Mutes all members that are currently connected to the same voice chat you are.")
@commands.guild_only()
@has_mute_role()
async def mute(ctx):
    guild = get_guild_config(ctx.guild.id)
    if ctx.message.author.voice and ctx.message.author.voice.channel:
        print_log("Triggered mute in Guild", ctx.guild)
        channel = ctx.message.author.voice.channel
        await react(ctx)
        guild.is_muted = True
        for member in channel.members:
            await member.edit(mute=True)
        print_log("Muted", str(len(channel.members)), "Members")
        await delete_message(ctx)
    else:
        await react(ctx, False)
        await ctx.send("You need to be connected to a voice chat to use this command.")
        await delete_message(ctx)


@bot.command(aliases=["um", "u"], brief="Un-mutes all members in a voice chat",
             description="Un-mutes all members that are currently connected to the same voice chat you are.")
@commands.guild_only()
@has_mute_role()
async def unmute(ctx):
    guild = get_guild_config(ctx.guild.id)

    if ctx.message.author.voice and ctx.message.author.voice.channel:
        print_log("Triggered unmute in Guild", ctx.guild)
        channel = ctx.message.author.voice.channel
        await react(ctx)
        guild.is_muted = False
        for member in channel.members:
            await member.edit(mute=False)
        print_log("Un-muted", str(len(channel.members)), "Members")
        await delete_message(ctx)
    else:
        await react(ctx, False)
        await ctx.send("You need to be connected to a voice chat to use this command.")
        await delete_message(ctx)


@bot.group(aliases=["cfg", "settings"], brief="Changes the bot settings for the guild",
           description="Subcommands to change settings of the bot: mute_role, game_channel, dead_channel, block_mute")
# todo add remaining subcommands
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def config(ctx):
    if not isinstance(ctx.channel, discord.TextChannel):
        await react(ctx, False)
        await ctx.send("This command does not work in DMs.")
        await delete_message(ctx)
        return
    if ctx.invoked_subcommand is None:
        await react(ctx, False)
        await ctx.send("This command requires at least one argument.")
        await delete_message(ctx)
        return


@config.command()
async def mute_role(ctx, new_role_name: str):

    guild = get_guild_config(ctx.guild.id)
    old_role_name = guild.mute_permissions_role
    if new_role_name == old_role_name:
        await react(ctx, False)
        await ctx.send("The new role-name has to differ from the old one")
        return
    await react(ctx)
    guild.mute_permissions_role = new_role_name
    print_log("Changed mute-role of guild ", guild.name, "from", old_role_name, "to", new_role_name)
    save_guilds()
    await ctx.send("Changed the mute-role from '{0}' to '{1}'.".format(old_role_name, new_role_name))

    await delete_message(ctx)


# ------------------- OWNER COMMANDS -------------------
@bot.command(aliases=["d"], brief="Disables the bot",
             description="Disables all commands and listeners of the bot except for {0}status.".format(PREFIX))
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


@bot.command(aliases=["e"], brief="Enables the bot",
             description="Enables all commands and listeners of the bot.")
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
    if isinstance(error, commands.errors.NoPrivateMessage):
        await ctx.send(error)
        return
    elif isinstance(error, commands.errors.CheckFailure):
        guild = get_guild_config(ctx.guild.id)
        await ctx.send("You need to have the role '{0}' to use this command.".format(guild.mute_permissions_role))
        print_log("Mute Role error of User", ctx.message.author, "in Guild", ctx.guild)
        await delete_message(ctx)


@disable.error
@enable.error
@config.error
async def no_permission_error(ctx, error):
    await react(ctx, False)
    if isinstance(error, commands.errors.NoPrivateMessage):
        await ctx.send(error)
        return
    elif isinstance(error, commands.errors.CheckFailure):
        await ctx.send("You don't have permissions to do that.")
        print_log("No permission error of User", ctx.message.author, "in Guild", ctx.guild)
        await delete_message(ctx)


@mute_role.error
async def required_argument_missing_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await react(ctx, False)
        await ctx.send(error)


bot.run(TOKEN)
