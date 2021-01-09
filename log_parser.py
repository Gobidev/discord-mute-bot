import glob
import os.path


def combine_logs():
    all_log_files = glob.glob(os.path.join(os.getcwd(), "*.log.*"))
    all_log_files.append(os.path.join(os.getcwd(), "Bot.log"))
    with open("all_logs.log", "w", encoding='utf8') as f:
        for file_name in all_log_files:
            f.write(open(file_name, "r", encoding='utf8').read())


def read_log(log_name: str) -> list:
    with open(log_name, "r", encoding='utf8') as f:
        all_lines = [n[:-1] for n in f.readlines()]
    log = [(line[:19], line[20:]) for line in all_lines]
    return log


def get_join_and_leave_times(log: list) -> list:
    events = []
    guild_count = 0
    for entry in log:
        if "Joined guild" in entry[1]:
            guild_count += 1
            events.append((entry[0], guild_count))
        elif "Left guild" in entry[1]:
            guild_count -= 1
            events.append((entry[0], guild_count))
    return events


def get_mute_times(log: list) -> list:
    events = []
    mute_count = 0
    for entry in log:
        if "Muted" in entry[1]:
            entry_words = entry[1].split(" ")
            try:
                amount = int(entry_words[1])
                mute_count += amount
                events.append((entry[0], mute_count))
            except ValueError:
                mute_count += 1
                events.append((entry[0], mute_count))
    return events


def get_time_info(entry_: tuple) -> list:
    timestamp = entry_[0]
    d, t = timestamp.split(" ")
    out_str = d.split("-") + t.split(":")
    out_int = [int(n) for n in out_str]
    return out_int


def print_time_stamps_to_csv(log: list, filename: str):
    with open(filename, "w") as f:
        for entry in log:
            f.write(entry[0] + "," + str(entry[1]) + "\n")


if __name__ == '__main__':
    combine_logs()
    print_time_stamps_to_csv(get_join_and_leave_times(read_log("all_logs.log")), "guild_count.csv")
    print_time_stamps_to_csv(get_mute_times(read_log("all_logs.log")), "mute_count.csv")
