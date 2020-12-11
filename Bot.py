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
LOGGING = False


# ------------------- DO NOT EDIT THIS -------------------
def print_log(*args, **kwargs):
    """Print content to file and console along with a timestamp. Has the exact same syntax as print()"""
    t = time.strftime("%Y-%m-%d %T")
    print(t, *args, **kwargs)
    with open('Bot.log', 'a') as file:
        try:
            print(t, *args, **kwargs, file=file)
        except UnicodeEncodeError:
            print_log("Error writing log entry")


def load_guilds():
    """Load configuration of guilds from file with the pickle module"""
    global guilds
    if os.path.isfile("guilds.config"):
        with open("guilds.config", "rb") as config_file:
            guilds = pickle.load(config_file)
        print_log("Loaded {0} guild-configs from file".format(len(guilds)))


def save_guilds():
    """Save configuration of guilds to file with the pickle module"""
    global guilds
    with open("guilds.config", "wb") as config_file:
        pickle.dump(guilds, config_file)
    print_log("Saved config of {0} guilds to file".format(len(guilds)))


def get_guild_config(guild_id):
    """Return a guild configuration for a given guild_id"""
    global guilds
    for guild in guilds:
        if guild.guild_id == guild_id:
            return guild


class Guild:
    """Class to save the configuration for individual guilds"""
    def __init__(self, guild):
        self.name = str(guild)
        self.guild_id = guild.id
        self.is_muted = False
        self.game_channel_name = "Crew"
        self.dead_channel_name = "Ghosts"
        self.mute_permissions_role = "Mute Master"
        self.block_server_mute = False
        self.game_codes = []
        self.game_code_channel_id = None

        print_log("Added guild", self.name)


class GameCode:
    """Class to save author of game code messages"""
    def __init__(self, message1_id, message2_id, channel_id, author_id):
        self.message1_id = message1_id
        self.message2_id = message2_id
        self.channel_id = channel_id
        self.author_id = author_id


DISABLED = False
guilds = []
load_guilds()

bot = commands.Bot(command_prefix=PREFIX)


# ------------------- EVENTS -------------------
@bot.event
async def on_ready():
    global guilds
    print_log('Logged in as {0.user}'.format(bot))

    """Generate guild configs for new guilds"""
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

    await stop_all_games()
    await update_default_activity()


@bot.event
async def on_message(message):
    """Logging of text messages on guilds if logging is enabled and deleting messages of the bot that are neither an
    embed nor a mono-font message i.e. used in the help command. This mostly includes error messages."""

    if isinstance(message.channel, discord.TextChannel):
        guild = get_guild_config(message.channel.guild.id)

        if LOGGING:
            print_log("{1}: '{0}' (in channel {2} on guild {3})".format(message.content, message.author,
                                                                        message.channel, message.channel.guild))
        if message.content.startswith(PREFIX):
            print_log("{1}: '{0}' (in channel {2} on guild {3})".format(message.content, message.author,
                                                                        message.channel, message.channel.guild))
        if guild.game_code_channel_id is not None:
            if guild.game_code_channel_id == message.channel.id and len(message.content) == 6:
                await code(await bot.get_context(message), message.content)
    if message.author == bot.user:
        if message.content != "" and not message.content.startswith("```"):
            await asyncio.sleep(8)
            try:
                await message.delete()
            except discord.errors.Forbidden:
                pass
    else:
        await bot.process_commands(message)


@bot.event
async def on_guild_join(guild):
    """Generating a config for guilds on guild join."""
    global guilds
    print_log("Joined guild", guild)

    guilds.append(Guild(guild))
    print_log("Added config for guild", guild)
    save_guilds()

    await update_default_activity()


@bot.event
async def on_guild_remove(guild):
    """Update the activity when leaving a guild"""
    print_log("Left guild", guild)
    await update_default_activity()


@bot.event
async def on_command_error(ctx, error):
    """Printing all error messages and sending an error when command is not found."""
    print_log(error)
    if isinstance(error, commands.errors.CommandNotFound):
        await react(ctx, False)
        if ctx.message.content.startswith(".["):
            await ctx.send("```Please use only one of the command options. Example: If the command is .[mute|m], you "
                           "can either use .mute or .m to use the command.```")


@bot.event
async def on_voice_state_update(member, before, after):
    """Muting and un-muting members according to what voice channel they are in."""
    if DISABLED:
        return

    if after.channel is not None:
        guild = get_guild_config(after.channel.guild.id)
    else:
        guild = get_guild_config(before.channel.guild.id)

    # Only log voice channel updates when the actual channel changed
    if before.channel is not after.channel:
        if LOGGING:
            print_log("Voice channel change: {0} from {1} to {2} on Guild {3}".format(
                member, before.channel, after.channel, guild.name))
    else:
        # A voice channel update without a change in channel does not affect the bot unless block_server_mute is enabled
        # for the server, therefore return if it is not enable
        if not guild.block_server_mute:
            return

    # According to what channel the member joined and if server-mute is active, it is either muted or un-muted
    if str(after.channel) != guild.game_channel_name and member.voice.mute:
        # Member is un-muted when joining the dead-channel and was muted before
        await member.edit(mute=False)
        print_log("Un-muted member", member, "in channel", after.channel, "on guild", guild.name)

    elif str(after.channel) == guild.game_channel_name:
        if guild.is_muted and not member.voice.mute:
            # if the member joins the game channel, mute is active and the member was not muted before, it is muted
            await member.edit(mute=True)
            print_log("Muted member", member, "in channel", after.channel, "on guild", guild.name)


@bot.event
async def on_reaction_add(reaction, user):

    # Test if bot reacted to message
    if user == bot.user:
        return

    message = reaction.message
    guild = get_guild_config(message.channel.guild.id)
    all_reactions = message.reactions

    valid = False
    is_admin = False
    is_author = False

    for r in all_reactions:
        if str(r) == "❌":
            async for u in r.users():
                if u == bot.user:
                    valid = True

    # Test if user is admin
    if valid and ('administrator', True) in user.permissions_in(message.channel):
        is_admin = True

    game = None
    for game_code in guild.game_codes:
        if game_code.message2_id == message.id:
            game = game_code

    if game is None:
        return

    # Test if user is author
    if game.author_id == user.id:
        is_author = True

    if is_admin or is_author:
        message1 = await message.channel.fetch_message(game.message1_id)
        message2 = await message.channel.fetch_message(game.message2_id)
        await message1.delete()
        await message2.delete()

        del guild.game_codes[guild.game_codes.index(game)]
        save_guilds()


# ------------------- OTHER FUNCTIONS -------------------
def is_owner():
    """Check if a user is the bot owner"""
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID

    return commands.check(predicate)


def has_mute_role():
    """Check if a user has the role specified in the guild config to use mute and un-mute commands"""
    async def predicate(ctx):

        # Test if user is admin
        if ('administrator', True) in ctx.message.author.permissions_in(ctx.channel):
            return True

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


async def stop_all_games():
    """Set the mute attribute of all guild configs to False and all games to None, called at bot startup"""
    global guilds
    for guild in guilds:

        guild.is_muted = False

        if guild.game_codes:
            print_log("Delete old game code messages")

            for game_code in guild.game_codes:
                try:
                    channel = await bot.fetch_channel(game_code.channel_id)
                except discord.errors.Forbidden:
                    return 

                try:
                    message1 = await channel.fetch_message(game_code.message1_id)
                    message2 = await channel.fetch_message(game_code.message2_id)
                    await message1.delete()
                    await message2.delete()

                except discord.errors.NotFound:
                    pass

            guild.game_codes = []

    print_log("Stopped all running games")
    save_guilds()


async def react(ctx, accepted=True):
    """Reacting to a command message either with thumbs up if it was valid, or a no entry sign if an error occurred"""
    try:
        if accepted:
            await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
    except discord.errors.Forbidden:
        pass


@commands.guild_only()
async def delete_message(ctx):
    """Delete a member command after 1 second to keep channels clean, skipping when called in DMs."""
    await asyncio.sleep(1)
    try:
        await ctx.message.delete()
    except discord.errors.Forbidden:
        pass


async def update_default_activity():
    """Update the number of guilds the bot is active on in the bot activity."""
    activity = "muting on {0} guilds".format(len(bot.guilds))
    await bot.change_presence(activity=discord.Game(activity))


# ------------------- COMMANDS -------------------
@bot.command(aliases=["ping", "info", "p"], brief="Shows the current status of the bot",
             description="Shows if the bot is active, current ping time, CPU and RAM usage, number of guilds and the"
                         "number of users the bot has.")
async def status(ctx):
    """Send an embed containing current information of the bot"""
    await react(ctx)
    embed = discord.Embed(title="Bot Status", color=discord.Color.orange())
    embed.add_field(name="Status", value=":red_circle: Disabled" if DISABLED else ":green_circle: Enabled")
    embed.add_field(name="Ping", value=":clock1: " + str(round(bot.latency * 1000)) + "ms")
    embed.add_field(name="CPU", value=":desktop: " + str(psutil.cpu_percent()) + "%")
    embed.add_field(name="RAM", value=":film_frames: " + str(round(psutil.virtual_memory().used * 10 ** -9, 2)) +
                                      "GB/" + str(round(psutil.virtual_memory().total * 10 ** -9, 2)) + "GB")
    embed.add_field(name="Guilds", value=":house: " + str(len(bot.guilds)))
    # calculate the number of users of the bot
    amount_users = 0
    for guild in bot.guilds:
        for _ in guild.members:
            amount_users += 1
    embed.add_field(name="Users", value=":people_holding_hands: " + str(amount_users))
    # If bot is not ready, creator will be None
    await bot.wait_until_ready()
    # do not change this creator code
    creator = await bot.fetch_user(480284798028611584)
    embed.set_footer(text="made by {0}".format(creator), icon_url=creator.avatar_url)
    await ctx.send(embed=embed)
    await delete_message(ctx)


@bot.command(aliases=["m"], brief="Mutes all members in a voice chat",
             description="Mutes all members that are currently connected to the same voice chat you are.")
@commands.guild_only()
@has_mute_role()
async def mute(ctx):
    if DISABLED:
        return

    guild = get_guild_config(ctx.guild.id)

    # Test if member is connected to a voice chat
    if ctx.message.author.voice:

        # Test if the name of the voice chat equals the game chat of the guild config
        if str(ctx.message.author.voice.channel) == guild.game_channel_name:
            print_log("Triggered mute in Guild", ctx.guild)
            channel = ctx.message.author.voice.channel
            await react(ctx)
            guild.is_muted = True

            t1 = time.time()
            tasks = [asyncio.create_task(member.edit(mute=True)) for member in channel.members]
            await asyncio.gather(*tasks)
            t2 = time.time()

            print_log("Muted", str(len(channel.members)), "Members. Time:", str(round(t2 - t1, 2)) + "s")
            await delete_message(ctx)
        else:
            await react(ctx, False)
            await ctx.send("Please join a channel named '{0}' to use this command.".format(guild.game_channel_name))
            await delete_message(ctx)
    else:
        await react(ctx, False)
        await ctx.send("Please join a voice chat to use this command.")
        await delete_message(ctx)


@bot.command(aliases=["um", "u"], brief="Un-mutes all members in a voice chat",
             description="Un-mutes all members that are currently connected to the same voice chat you are.")
@commands.guild_only()
@has_mute_role()
async def unmute(ctx):
    if DISABLED:
        return

    guild = get_guild_config(ctx.guild.id)

    # Test if member is connected to a voice chat
    if ctx.message.author.voice:

        # Test if the name of the voice chat equals the game chat of the guild config
        if str(ctx.message.author.voice.channel) == guild.game_channel_name:
            print_log("Triggered unmute in Guild", ctx.guild)
            channel = ctx.message.author.voice.channel
            await react(ctx)
            guild.is_muted = False

            t1 = time.time()
            tasks = [asyncio.create_task(member.edit(mute=False)) for member in channel.members]
            await asyncio.gather(*tasks)
            t2 = time.time()

            print_log("Un-muted", str(len(channel.members)), "Members. Time:", str(round(t2 - t1, 2)) + "s")
            await delete_message(ctx)
        else:
            await react(ctx, False)
            await ctx.send("Please join a channel named '{0}' to use this command.".format(guild.game_channel_name))
            await delete_message(ctx)
    else:
        await react(ctx, False)
        await ctx.send("Please join a voice chat to use this command.")
        await delete_message(ctx)


@bot.command(aliases=["i", "inv"], brief="Sends the invite-url for the bot",
             description="Send an embed containing an invite-url for the bot to add it to a server.")
async def invite(ctx):
    embed = discord.Embed(title="Invite this bot")
    embed.add_field(name="URL",
                    value="Click [here](https://discord.com/api/oauth2/authorize?client_id=764824685581565963&"
                          "permissions=315190352&scope=bot)")
    # If bot is not ready, creator will be None
    await bot.wait_until_ready()
    # do not change this creator code
    creator = await bot.fetch_user(480284798028611584)
    embed.set_footer(text="made by {0}".format(creator), icon_url=creator.avatar_url)
    await ctx.send(embed=embed)
    await delete_message(ctx)


@bot.command(aliases=["c", "game", "host"], brief="Show an Among Us game code in a nice way",
             description="Send an embed containing the game code, map and region of a hosted Among Us game.")
async def code(ctx, game_code: str, map_name=None, region=None):
    if DISABLED:
        return

    guild = get_guild_config(ctx.guild.id)

    # noinspection SpellCheckingInspection
    maps = {"skeld": "The Skeld", "polus": "Polus", "mira": "Mira HQ"}
    regions = {"eu": "Europe", "na": "North America", "asia": "Asia"}

    # Check if code has the length of 6 (typical Among Us code length)
    if not len(game_code) == 6:
        await react(ctx, False)
        await ctx.send("Please enter a valid game code.")
        await delete_message(ctx)
        return

    game_code = game_code.upper()

    if map_name not in maps or map_name is None:
        map_output = "?"
    else:
        map_output = maps[map_name]

    if region not in regions or region is None:
        region_output = "?"
    else:
        region_output = regions[region]

    await react(ctx)

    author = ctx.message.author

    embed = discord.Embed(title=game_code, color=0x3700ff)
    embed.add_field(name="**Map:**", value=map_output)
    embed.add_field(name="**Region:**", value=region_output)

    embed.set_footer(text="Game hosted by {0}".format(author), icon_url=author.avatar_url)

    embed_message = await ctx.send(embed=embed)
    # Send game code as pure string in addition to embed to be copyable for mobile users
    code_message = await ctx.send("```" + game_code + "```")

    await code_message.add_reaction("❌")

    print_log("Create game in guild", guild.name, "({0}, {1}, {2})".format(game_code, map_output, region_output))

    guild.game_codes.append(GameCode(embed_message.id, code_message.id, ctx.channel.id, author.id))
    save_guilds()

    await delete_message(ctx)


@bot.group(aliases=["cfg", "settings"], brief="Changes the bot config for this guild",
           description="Command to change settings of the bot for this guild.")
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def config(ctx):
    if DISABLED:
        return

    if ctx.invoked_subcommand is None:
        await react(ctx, False)
        await ctx.send("This command requires at least one argument. Use '{0}help config' for further information"
                       .format(PREFIX))
        await delete_message(ctx)
        return


@config.command(aliases=["mr", "mute-role", "permissions_role"], brief="Change the mute role of this guild",
                description="Change the role that is required to use the mute and un-mute commands.")
async def mute_role(ctx, new_role_name: str):
    """Change the mute role of a guild-config"""

    guild = get_guild_config(ctx.guild.id)

    old_role_name = guild.mute_permissions_role
    if new_role_name == old_role_name:
        await react(ctx, False)
        await ctx.send("The new role-name has to differ from the old one")
        await delete_message(ctx)
        return
    await react(ctx)
    guild.mute_permissions_role = new_role_name
    print_log("Changed mute-role of guild ", guild.name, "from", old_role_name, "to", new_role_name)
    save_guilds()
    await ctx.send("Changed the mute-role from '{0}' to '{1}'.".format(old_role_name, new_role_name))

    await delete_message(ctx)


async def change_channel(ctx, new, channel_type):
    """Change either dead-channel or game-channel of guild config."""
    guild = get_guild_config(ctx.guild.id)

    if guild.is_muted:
        await react(ctx, False)
        await ctx.send("This setting cannot be changed while mute is active.")
        return

    if channel_type == "game":
        old = guild.game_channel_name
        old2 = guild.dead_channel_name
    else:
        old = guild.dead_channel_name
        old2 = guild.game_channel_name

    if new == old:
        await react(ctx, False)
        await ctx.send("The new channel name has to differ from the old one.")
        return

    if new == old2:
        await react(ctx, False)
        await ctx.send("The game channel cannot be the same as the dead channel.")
        return

    await react(ctx)
    if channel_type == "game":
        guild.game_channel_name = new
        print_log("Changed game-channel of guild ", guild.name, "from", old, "to", new)
        await ctx.send("Changed the game-channel from '{0}' to '{1}'.".format(old, new))
    else:
        guild.dead_channel_name = new
        print_log("Changed dead-channel of guild ", guild.name, "from", old, "to", new)
        await ctx.send("Changed the dead-channel from '{0}' to '{1}'.".format(old, new))

    save_guilds()


@config.command(aliases=["gc", "game-channel", "game"], brief="Change the game-channel of this guild",
                description="Change the channel name that is affected by the mute and unmute commands.")
async def game_channel(ctx, new_game_channel: str):
    await change_channel(ctx, new_game_channel, "game")
    await delete_message(ctx)


@config.command(aliases=["dc", "dead-channel", "dead"], brief="Change the game-channel of this guild",
                description="Change the channel name that is automatically un-muted on join.")
async def dead_channel(ctx, new_dead_channel: str):
    await change_channel(ctx, new_dead_channel, "dead")
    await delete_message(ctx)


@config.command(aliases=["bm", "block", "toggle", "block-mute"], brief="Toggle if server mute suppression is active",
                description="Set the suppression of server mutes of other users to active or inactive.")
async def block_mute(ctx):
    guild = get_guild_config(ctx.guild.id)

    await react(ctx)
    if guild.block_server_mute:
        guild.block_server_mute = False
        await ctx.send("Server mute is no longer blocked")
        print_log("Server mute is no longer blocked in guild", guild.name)
    else:
        guild.block_server_mute = True
        await ctx.send("Server mute will now be blocked")
        print_log("Server mute will now be blocked in guild", guild.name)

    save_guilds()
    await delete_message(ctx)


@config.command(aliases=["cc", "code-channel", "codes", "set-code-channel"],
                brief="Set a channel to be used for Among Us game codes",
                description="Specify a text channel for this guild in which sent game codes will be converted to"
                            "embeds.")
async def set_code_channel(ctx):
    guild = get_guild_config(ctx.guild.id)

    await react(ctx)
    guild.game_code_channel_id = ctx.channel.id
    save_guilds()
    await delete_message(ctx)


# ------------------- OWNER COMMANDS -------------------
@bot.command(aliases=["d"], brief="Disables the bot",
             description="Disables all commands and events of the bot except for {0}status.".format(PREFIX))
@is_owner()
async def disable(ctx):
    """Disables all commands and events of the bot."""
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
             description="Enables all commands and events of the bot.")
@is_owner()
async def enable(ctx):
    """Enables all commands and events of the bot."""
    global DISABLED
    if not DISABLED:
        await react(ctx, False)
        await ctx.send("The Bot is already enabled.")
        await delete_message(ctx)
        return
    await react(ctx)
    DISABLED = False
    print_log("Bot is now enabled")
    await update_default_activity()
    await delete_message(ctx)


# ------------------- ERROR HANDLING -------------------

@mute.error
@unmute.error
async def mute_error(ctx, error):
    """Called when an error in mute() or unmute() occurs, send error message to member."""
    await react(ctx, False)
    # Check if command was called in DMs
    if isinstance(error, commands.errors.NoPrivateMessage):
        await ctx.send(error)
        return
    # Check if member did not have the permissions to use the command
    elif isinstance(error, commands.errors.CheckFailure):
        guild = get_guild_config(ctx.guild.id)
        await ctx.send("You need to have the role '{0}' to use this command.".format(guild.mute_permissions_role))
        print_log("Mute Role error of User", ctx.message.author, "in Guild", ctx.guild)
        await delete_message(ctx)


@disable.error
@enable.error
@config.error
async def no_permission_error(ctx, error):
    """Called when error in any owner-only-command occurs, send error message to member."""
    await react(ctx, False)
    # Check if command was used in private messages, which does not work for config()
    if isinstance(error, commands.errors.NoPrivateMessage):
        await ctx.send(error)
        return
    # Check if member did not have the permissions to use the command
    elif isinstance(error, commands.errors.CheckFailure):
        await ctx.send("You don't have permissions to do that.")
        print_log("No permission error of User", ctx.message.author, "in Guild", ctx.guild)
        await delete_message(ctx)


@mute_role.error
@code.error
async def required_argument_missing_error(ctx, error):
    """Called when an error occurs in any settings subcommand, send error message to member."""
    # Check if required argument for command was missing
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await react(ctx, False)
        await ctx.send(error)
        await delete_message(ctx)


bot.run(TOKEN)
