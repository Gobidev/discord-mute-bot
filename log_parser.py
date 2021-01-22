import glob
import time
import datetime
import os.path


def combine_logs():
    all_log_files = glob.glob(os.path.join(os.getcwd(), "logs", "*.log.*"))
    if os.path.isfile(os.path.join("logs", "Bot.log")):
        all_log_files.append(os.path.join(os.getcwd(), os.path.join("logs", "Bot.log")))

    # sort files
    files_with_times = {}
    for log_file in all_log_files:
        first_line_time = get_time_info(read_log(log_file)[0])
        files_with_times[log_file] = first_line_time
    filenames_sorted = [k for k, v in sorted(files_with_times.items(), key=lambda item: item[1])]

    with open(os.path.join("logs", "all_logs.log"), "w", encoding='utf8') as f:
        for file_name in filenames_sorted:
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


def get_time_info(entry_: tuple) -> float:
    timestamp = entry_[0]
    d, t = timestamp.split(" ")
    out_str = d.split("-") + t.split(":")
    out_int = [int(n) for n in out_str]
    return time.mktime(datetime.datetime(*out_int).timetuple())


def print_time_stamps_to_csv(log: list, filename: str):
    with open(filename, "w") as f:
        for entry in log:
            f.write(entry[0] + "," + str(entry[1]) + "\n")


if __name__ == '__main__':
    if not os.path.isdir("logs"):
        print("No logs found")
        exit()
    if not os.path.isdir("parser_output"):
        os.mkdir("parser_output")

    combine_logs()
    print_time_stamps_to_csv(get_join_and_leave_times(read_log(os.path.join("logs", "all_logs.log"))),
                             os.path.join("parser_output", "guild_count.csv"))
    print_time_stamps_to_csv(get_mute_times(read_log(os.path.join("logs", "all_logs.log"))),
                             os.path.join("parser_output", "mute_count.csv"))
