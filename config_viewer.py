import os
import pickle

guilds = []


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


class GameCode:
    """Class to save author of game code messages"""
    def __init__(self, message1_id, message2_id, channel_id, author_id):
        self.message1_id = message1_id
        self.message2_id = message2_id
        self.channel_id = channel_id
        self.author_id = author_id


def load_guilds():
    """Load configuration of guilds from file with the pickle module"""
    global guilds
    if os.path.isfile("guilds.config"):
        with open("guilds.config", "rb") as config_file:
            guilds = pickle.load(config_file)


def save_guilds():
    """Save configuration of guilds to file with the pickle module"""
    global guilds
    with open("guilds.config", "wb") as config_file:
        pickle.dump(guilds, config_file)


def generate_csv():
    global guilds
    output_file = open("out.csv", "w", encoding='utf8')
    for guild in guilds:
        guild_dict = dict(guild.__dict__.items())
        first = True
        for attribute in guild_dict:
            if not first:
                output_file.write(", ")
            output_file.write(str(guild_dict[attribute]).replace(",", "."))
            first = False
        output_file.write("\n")
    output_file.close()


def remove_duplicates():
    global guilds
    load_guilds()
    all_guild_ids = []
    for guild in guilds:
        all_guild_ids.append(guild.guild_id)
    double_ids = list(set([x for x in all_guild_ids if all_guild_ids.count(x) > 1]))
    print(len(guilds))
    for double_id in double_ids:
        for guild in guilds:
            if guild.guild_id == double_id:
                del guilds[guilds.index(guild)]
    print(len(guilds))
    save_guilds()


def get_all_ids_from_csv():
    try:
        with open("out.csv", "r", encoding='utf-8') as f:
            all_data = [n.replace("\n", "") for n in f.readlines()]
    except FileNotFoundError:
        print("Please generate csv first")
    all_ids = [int(n.split(",")[1]) for n in all_data]
    print(all_ids)
    print(len(all_ids))
    duplicates = list(set([x for x in all_ids if all_ids.count(x) > 1]))
    print(duplicates)
    print(len(duplicates))
    return all_ids


if __name__ == '__main__':
    remove_duplicates()
