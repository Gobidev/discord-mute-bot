import glob
import os.path


# Rename Bot.log to avoid large file sizes
if __name__ == '__main__':
    all_archive_files = glob.glob(os.path.join(os.getcwd(), "logs", "*.log.*"))
    current_max = max([int(n.split(".")[-1]) for n in all_archive_files])
    os.rename(os.path.join("logs", "Bot.log"), os.path.join("logs", "Bot.log.{0}".format(current_max + 1)))
    print("Renamed Bot.log ->", "Bot.log.{0}".format(current_max + 1))
